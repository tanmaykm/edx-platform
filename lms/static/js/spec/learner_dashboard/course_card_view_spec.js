define([
        'backbone',
        'jquery',
        'js/learner_dashboard/models/course_card_model',
        'js/learner_dashboard/views/course_card_view'
    ], function (Backbone, $, CourseCardModel, CourseCardView) {
        
        'use strict';
        
        describe('Course Card View', function () {
            var view = null,
                courseCardModel,
                setupView,
                context = {      
                    course_modes: [],
                    display_name: 'Astrophysics: Exploring Exoplanets',
                    key: 'ANU-ASTRO1x',
                    marketing_url: 'https://www.edx.org/course/astrophysics-exploring-exoplanets-anux-anu-astro2x-1',
                    organization: {
                        display_name: 'Australian National University',
                        key: 'ANUx'
                    },
                    run_modes: [{
                        course_start: 'Apr 25, 2016',
                        course_end: 'Jun 13, 2016',
                        course_key: 'course-v1:ANUx+ANU-ASTRO1x+3T2015',
                        courseware_url: 'http://localhost:8000/courses/course-v1:edX+DemoX+Demo_Course/info',
                        image_url: 'https://www.edx.org/sites/default/files/styles/course_video_banner/public/course/image/featured-card/italian1x-video_still_318x210.jpg?itok=l_bMTvC9',
                        mode_slug: 'verified',
                        run_key: '2T2016',
                        course_started: true,
                        enrollment_status: 'enrolled',
                        certificate_url: '',
                    }]
                };

            setupView = function(enrollment_status){
                context.run_modes[0].enrollment_status = enrollment_status;
                setFixtures('<div class="course-card card"></div>');
                courseCardModel = new CourseCardModel(context);
                view = new CourseCardView({
                    model: courseCardModel
                });
            };

            beforeEach(function() {
                setupView(null);
            });

            afterEach(function() {
                view.remove();
            });

            it('should exist', function() {
                expect(view).toBeDefined();
            });

            it('should render the course card based on the data enrolled', function() {
                view.remove();
                setupView('enrolled');
                expect(view.$('.header-img').attr('src')).toEqual(context.run_modes[0].image_url);
                expect(view.$('.course-details .course-title-link').text().trim()).toEqual(context.display_name);
                expect(view.$('.course-details .course-title-link').attr('href')).toEqual(context.marketing_url);
                expect(view.$('.course-details .course-text .course-key').html()).toEqual(context.key);
                expect(view.$('.course-details .course-text .run-period').html())
                    .toEqual(context.run_modes[0].course_start + ' - ' + context.run_modes[0].course_end);
            });

            it('should render the course card based on the data not enrolled', function() {
                expect(view.$('.header-img').attr('src')).toEqual(context.run_modes[0].image_url);
                expect(view.$('.course-details .course-title-link').text().trim()).toEqual(context.display_name);
                expect(view.$('.course-details .course-title-link').attr('href')).toEqual(context.marketing_url);
                expect(view.$('.course-details .course-text .course-key').html()).toEqual(context.key);
                expect(view.$('.course-details .course-text .run-period').html()).not.toBeDefined();
            });
        });
    }
);
