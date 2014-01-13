module.exports = function(grunt){
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
    browserify: {
      dist: {
        files: {
          'inthe_am/taskmanager/static/task_manager.js': [
              'inthe_am/taskmanager/static/modules/*.js'
          ]
        },
        options: {
        }
      }
    },
    ember_handlebars: {
      compile: {
        options: {
          processName: function(name) {
            return name.substr(
              name.lastIndexOf('/') + 1,
              name.lastIndexOf('.') - name.lastIndexOf('/') - 1
            ).replace('__', '/');
          }
        },
        files: {
          'inthe_am/taskmanager/static/templates.js': [
            'inthe_am/taskmanager/static/modules/templates/*.hbs'
          ]
        }
      }
    },
    sass: {
      dist: {
        files: {
          'inthe_am/taskmanager/static/main.css': 'inthe_am/taskmanager/static/scss/main.scss'
        }
      }
    },
    watch: {
      sass: {
        files: [
          'inthe_am/taskmanager/static/scss/*.scss',
        ],
        tasks: [
          'sass'
        ]
      },
      jscript: {
        files: [
          'inthe_am/taskmanager/static/modules/**/*.js',
        ],
        tasks: [
          'browserify'
        ]
      },
      handlebars: {
        files: [
          'inthe_am/taskmanager/static/modules/**/*.hbs'
        ],
        tasks: [
          'ember_handlebars',
        ]
      }
    }
  });

  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-browserify');
  grunt.loadNpmTasks('grunt-ember-handlebars');
  grunt.loadNpmTasks('grunt-sass');

};