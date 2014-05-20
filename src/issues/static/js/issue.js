"use strict";

$(function() {

    function refreshButtons(commentEmpty) {
        $('.add-comment-btn').prop('disabled', commentEmpty);
        $('.close-issue-btn').prop('disabled', !commentEmpty);
    }

    if ($('.htmlarea textarea').length) {
        var editor = $('.htmlarea textarea').ocdEditor().data('wysihtml5').editor;

        editor.on('input',  function() {
            refreshButtons(editor.getValue().trim() == '');
        });
    }

    // Comments

    // Add comment form
    $('#add-comment').ajaxForm({
        beforeSubmit: function(arr, form) {
            if (!$('#id_content').val()) {
                return false;
            }
        },
        success: function(data) {
            var el = $(data.trim());
            $("#add-comment").closest('li').before(el);
            $("#add-comment").get(0).reset();
            refreshButtons(true);
        }
    });

    // Delete and undelete comment form
    $('#comments').on('click', '.delete-comment button', function() {
        var btn = $(this);
        var form = btn.closest('form');
        var extra = {};
        if (btn.attr('name')) {
            extra[btn.attr('name')] = btn.attr('value');
        }
        form.ajaxSubmit({
                            data: extra,
                            success: function(data) {
                                form.closest('li').toggleClass('deleted', data=='0');
                            }
                        });
        return false;
    });

    // Edit comment Form:

    //  - start edit
    $('#comments').on('click', '.edit-comment button', function() {
        $('li.rich_editor').hide();
        var btn = $(this);
        var li = btn.closest('li'); 
        li.addClass('editing');
        var el = $("<div>Loading...</div>");
        li.find('.comment-inner').hide().after(el);
        $.get(btn.data('url'), function(data) {
            el.html(data).find('.htmlarea textarea').wysihtml5({locale: "he-IL"});
        });
    });

    // - cancel edit
    $('#comments').on('click', '.cancel-edit-comment button', function() {
        $('li.rich_editor').show();
        var btn = $(this);
        var li = btn.closest('li'); 
        li.removeClass('editing');
        li.find('.comment-inner').show();
        li.find('.edit-issue-form').parent().remove();
    });

    // - save edits
    $('#comments').on('click', '.save-comment button', function(ev) {
        $('li.rich_editor').show();
        var btn = $(this);
        var form = btn.closest('form');
        if (!form.find('textarea').val()) {
            ev.preventDefault();
            return false;
        }
        form.ajaxSubmit(function(data) {
                            if (!data) {
                                return;
                            }
                            var new_li = $(data.trim());
                            form.closest('li').replaceWith(new_li);
                        });
        return false;
    });

    $('#issue-complete,#issue-archive').ajaxForm({
        success: function(data) {
            var target = window.location.protocol + '//' + window.location.host + window.location.pathname;
            window.location = target;
			// window.history.back();
        }
    });
    
    $('#issue-undo-complete').ajaxForm({
        success: function(data) {
        	location.reload();
            // var target = window.location.protocol + '//' + window.location.host + window.location.pathname;
            // window.location = target;
        }

    });

    // fill empty file title upon file selection
    $('body').on('change', 'input#id_file', function() {
        var title_inp = $(this).closest('form').find('input#id_title');
        if(title_inp.val().length > 0)
            return;
        var full_filename = $(this).val();
        var base_filename = '';
        title_inp.val(base_filename);
     });
});
