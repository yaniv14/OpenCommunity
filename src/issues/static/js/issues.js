"use strict";


/* use tabs instead of drop down for proposal type */
function init_proposal_tabs(with_issue) {
    var TYPE_NONE = 0;
    var TYPE_TASK = 1;
    var TYPE_RULE = 2;
    var TYPE_ADMIN = 3;

    var IDX_NONE = 0;
    var IDX_ADMIN = 1;
    var IDX_RULE = 2;
    var IDX_TASK = 3;

    $("ul#proposal-type li").on('click', function() {
        $(this).addClass('active').siblings().removeClass('active');
        var type_select = $('#id_proposal-type');
        var proposal_controls = $('#id_proposal-content,#id_proposal-title').closest('.form-group');
        var task_controls = $('#id_proposal-assigned_to,#id_proposal-due_by').closest('.form-group');
        var tags_control = $('#id_proposal-tags').closest('.form-group'); 
        var selected_idx = $(this).index();
        if (!with_issue) {
            selected_idx += 1;
        }
        if (selected_idx == IDX_NONE) {
            type_select.val('');
            proposal_controls.hide();
            task_controls.hide();
            tags_control.hide();
            $("[id^='id_proposal']").prop('required', false);
        } else {
            proposal_controls.show();
            if (selected_idx == IDX_ADMIN) {
                type_select.val(TYPE_ADMIN);
                task_controls.hide();
                tags_control.hide();
            } else if (selected_idx == IDX_RULE) {
                type_select.val(TYPE_RULE);
                task_controls.hide();
                tags_control.show();
            } else if (selected_idx == IDX_TASK) {
                type_select.val(TYPE_TASK);
                task_controls.show();
                tags_control.hide();
            }
            proposal_controls.prop('required', true);
        }
    });
}

function init_user_autocomplete(ac_url) {
    var tpl = '<p {{#board}}class="emp"{{/board}}>{{value}}</p>';

    $("[id$='assigned_to']").typeahead({
        prefetch : ac_url,
        cache: false,
        remote : ac_url + '?q=%QUERY',
        engine : Hogan,
        template : tpl
    }).css('background-color', '#fff');

   $("[id$='assigned_to']").on('typeahead:selected', function (object, datum) {
        // console.log(datum);
        $("[id$='assigned_to_user']").val(datum['user__id']);      
        
  });
}

function searchIssues(term, inp) {
    var context = inp.closest('[id^="by_"]');
    $(".issue-table tr", context).each(function() {
        $(this).toggle(!term || $('a', $(this)).text().indexOf(term) > 0);
    });
}
