define([
        'backbone',
        'jquery',
        'js/learner_dashboard/views/course_card_model',
        'js/learner_dashboard/views/course_card_actions'
    ], function (Backbone, $, CourseCardModel, CourseCardActions) {
        
        'use strict';
        
        describe('Course Card Actions', function () {
            var view = null,
                courseCardActionModel,
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
                context.enrollment_status = enrollment_status;
                setFixtures('<div class="course-actions"></div>');
                courseCardModel = new CourseCardModel(context);
                view = new CourseCardActions({
                    model: courseCardModel
                });
                $el.html(view.el);
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

            it('should render the course card actions based on the data enrolled', function() {
                view.remove();
                setupView('enrolled');
                expect(view.$('.enrollment-info').html()).toEqual('ENROLLED');
                expect(view.$('.view-course-link').attr('src')).toEqual(context.courseware_url);
                expect(view.$('.view-course-link').text().toEqual('View Course');
            });

            it('should render the course card actions based on the data not enrolled', function() {
                expect(view.$('.enrollment-info').html()).toEqual('NOT ENROLLED');
                expect(view.$('.view-course-link').attr('src')).toEqual(context.marketing_url);
                expect(view.$('.view-course-link').text().toEqual('Enroll Now');
            });
        });
    }
);
