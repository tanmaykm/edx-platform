"""
Test cases for image processing functions in the profile image package.
"""
from contextlib import closing
from itertools import product
import os
from tempfile import NamedTemporaryFile
import unittest

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.test import TestCase
from django.test.utils import override_settings
import ddt
import mock
from nose.plugins.attrib import attr
import piexif
from PIL import Image

from ..exceptions import ImageValidationError
from ..images import (
    create_profile_images,
    remove_profile_images,
    validate_uploaded_image,
    _get_exif_orientation,
    _get_valid_file_types,
)
from .helpers import make_image_file, make_uploaded_file


@attr(shard=2)
@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Profile Image API is only supported in LMS')
class TestValidateUploadedImage(TestCase):
    """
    Test validate_uploaded_image
    """
    FILE_UPLOAD_BAD_TYPE = (
        u'The file must be one of the following types: {valid_file_types}.'.format(
            valid_file_types=_get_valid_file_types()
        )
    )

    def check_validation_result(self, uploaded_file, expected_failure_message):
        """
        Internal DRY helper.
        """
        if expected_failure_message is not None:
            with self.assertRaises(ImageValidationError) as ctx:
                validate_uploaded_image(uploaded_file)
            self.assertEqual(ctx.exception.message, expected_failure_message)
        else:
            validate_uploaded_image(uploaded_file)
            self.assertEqual(uploaded_file.tell(), 0)

    @ddt.data(
        (99, u"The file must be at least 100 bytes in size."),
        (100, ),
        (1024, ),
        (1025, u"The file must be smaller than 1 KB in size."),
    )
    @ddt.unpack
    @override_settings(PROFILE_IMAGE_MIN_BYTES=100, PROFILE_IMAGE_MAX_BYTES=1024)
    def test_file_size(self, upload_size, expected_failure_message=None):
        """
        Ensure that files outside the accepted size range fail validation.
        """
        with make_uploaded_file(
            dimensions=(1, 1), extension=".png", content_type="image/png", force_size=upload_size
        ) as uploaded_file:
            self.check_validation_result(uploaded_file, expected_failure_message)

    @ddt.data(
        (".gif", "image/gif"),
        (".jpg", "image/jpeg"),
        (".jpeg", "image/jpeg"),
        (".png", "image/png"),
        (".bmp", "image/bmp", FILE_UPLOAD_BAD_TYPE),
        (".tif", "image/tiff", FILE_UPLOAD_BAD_TYPE),
    )
    @ddt.unpack
    def test_extension(self, extension, content_type, expected_failure_message=None):
        """
        Ensure that files whose extension is not supported fail validation.
        """
        with make_uploaded_file(extension=extension, content_type=content_type) as uploaded_file:
            self.check_validation_result(uploaded_file, expected_failure_message)

    def test_extension_mismatch(self):
        """
        Ensure that validation fails when the file extension does not match the
        file data.
        """
        file_upload_bad_ext = (
            u'The file name extension for this file does not match '
            u'the file data. The file may be corrupted.'
        )
        # make a bmp, try to fool the function into thinking it's a jpeg
        with make_image_file(extension=".bmp") as bmp_file:
            with closing(NamedTemporaryFile(suffix=".jpeg")) as fake_jpeg_file:
                fake_jpeg_file.write(bmp_file.read())
                fake_jpeg_file.seek(0)
                uploaded_file = UploadedFile(
                    fake_jpeg_file,
                    content_type="image/jpeg",
                    size=os.path.getsize(fake_jpeg_file.name)
                )
                with self.assertRaises(ImageValidationError) as ctx:
                    validate_uploaded_image(uploaded_file)
                self.assertEqual(ctx.exception.message, file_upload_bad_ext)

    def test_content_type(self):
        """
        Ensure that validation fails when the content_type header and file
        extension do not match
        """
        file_upload_bad_mimetype = (
            u'The Content-Type header for this file does not match '
            u'the file data. The file may be corrupted.'
        )
        with make_uploaded_file(extension=".jpeg", content_type="image/gif") as uploaded_file:
            with self.assertRaises(ImageValidationError) as ctx:
                validate_uploaded_image(uploaded_file)
            self.assertEqual(ctx.exception.message, file_upload_bad_mimetype)


@attr(shard=2)
@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Profile Image API is only supported in LMS')
class TestGenerateProfileImages(TestCase):
    """
    Test create_profile_images
    """

    def check_exif_orientation(self, image, expected_orientation):
        """
        Check that the created object is a JPEG and that it has the expected
        """
        self.assertEqual(image.format, 'JPEG')
        if expected_orientation is not None:
            self.assertIn('exif', image.info)
            self.assertEqual(_get_exif_orientation(image.info['exif']), expected_orientation)
        else:
            self.assertIsNone(_get_exif_orientation(image.info.get('exif', piexif.dump({}))))

    @ddt.data(
        *product(
            ["gif", "jpg", "png"],
            [(1, 1), (10, 10), (100, 100), (1000, 1000), (1, 10), (10, 100), (100, 1000), (1000, 999)],
        )
    )
    @ddt.unpack
    def test_generation(self, image_type, dimensions):
        """
        Ensure that regardless of the input format or dimensions, the outcome
        of calling the function is square jpeg files with explicitly-requested
        dimensions being saved to the profile image storage backend.
        """
        extension = "." + image_type
        content_type = "image/" + image_type
        requested_sizes = {
            10: "ten.jpg",
            100: "hundred.jpg",
            1000: "thousand.jpg",
        }
        with make_uploaded_file(dimensions=dimensions, extension=extension, content_type=content_type) as uploaded_file:
            names_and_images = self._create_mocked_profile_images(uploaded_file, requested_sizes)
            actual_sizes = {}
            for name, image_obj in names_and_images:
                # get the size of the image file and ensure it's square jpeg
                width, height = image_obj.size
                self.assertEqual(width, height)
                actual_sizes[width] = name
            self.assertEqual(requested_sizes, actual_sizes)

    def test_jpeg_with_exif_orientation(self):
        requested_images = {10: "ten.jpg", 100: "hunnert.jpg"}
        rotate_90_clockwise = 8  # Value used in EXIF Orientation field.
        with make_image_file(orientation=rotate_90_clockwise, extension='.jpg') as imfile:
            for _, image in self._create_mocked_profile_images(imfile, requested_images):
                self.check_exif_orientation(image, rotate_90_clockwise)

    def test_jpeg_without_exif_orientation(self):
        requested_images = {10: "ten.jpg", 100: "hunnert.jpg"}
        with make_image_file(extension='.jpg') as imfile:
            for _, image in self._create_mocked_profile_images(imfile, requested_images):
                self.check_exif_orientation(image, None)

    def _create_mocked_profile_images(self, image_file, requested_images):
        """
        Create image files with mocked-out storage.

        Verifies that an image was created for each element in
        requested_images, and returns an iterator of 2-tuples representing
        those imageswhere each tuple consists of a filename and a PIL.Image
        object.
        """
        mock_storage = mock.Mock()
        with mock.patch(
            "openedx.core.djangoapps.profile_images.images.get_profile_image_storage",
            return_value=mock_storage,
        ):
            create_profile_images(image_file, requested_images)
        names_and_files = [v[0] for v in mock_storage.save.call_args_list]
        self.assertEqual(len(names_and_files), len(requested_images))
        for name, file_ in names_and_files:
            with closing(Image.open(file_)) as image:
                yield name, image


@attr(shard=2)
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Profile Image API is only supported in LMS')
class TestRemoveProfileImages(TestCase):
    """
    Test remove_profile_images
    """
    def test_remove(self):
        """
        Ensure that the outcome of calling the function is that the named images
        are deleted from the profile image storage backend.
        """
        requested_sizes = {
            10: "ten.jpg",
            100: "hundred.jpg",
            1000: "thousand.jpg",
        }
        mock_storage = mock.Mock()
        with mock.patch(
            "openedx.core.djangoapps.profile_images.images.get_profile_image_storage",
            return_value=mock_storage,
        ):
            remove_profile_images(requested_sizes)
            deleted_names = [v[0][0] for v in mock_storage.delete.call_args_list]
            self.assertEqual(requested_sizes.values(), deleted_names)
            mock_storage.save.reset_mock()
