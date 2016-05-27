/**
 * Model for Course Programs.
 */
(function (define) {
    'use strict';
    define([
            'backbone'
        ], 
        function (Backbone) {
        return Backbone.Model.extend({
            initialize: function(data) {
                if (data){
                    this.context = data;
                    //we should populate our model by looking at the run_modes
                    if (data.run_modes.length === 1){
                        //We only have 1 run mode for this program
                        this.setActiveRunMode(data.run_modes[0]);
                    }
                }
            },

            setActiveRunMode: function(runMode){
                this.set({
                    display_name: this.context.display_name,
                    marketing_url: this.context.marketing_url,
                    key: this.context.key,
                    course_start: runMode.course_start,
                    course_end: runMode.course_end,
                    enrollment_status: runMode.enrollment_status,
                    courseware_url: runMode.courseware_url,
                    image_url: runMode.image_url,
                    mode_slug: runMode.mode_slug
                });
            }
        });
    });
}).call(this, define || RequireJS.define);
