"use strict";

// TODO: refactor all file.


// $.fn.ocdEditor = function () {
//     this.init({
//         locale: OCD.language == 'he' ? "he-IL" : 'en',
//         selector: '.wysiwyg'
//         // stylesheets: OCD.language == 'he' ? [OCD.static + 'css/rtl.css'] : []
//     });
//     return this;
// };

// $.fn.enhanceHtml = function () {
//     this.find('.htmlarea textarea').ocdEditor().css({
//         'width': '100%',
//         'border-top-right-radius': '0',
//         'border-top-left-radius': '0'
//     });
//     return this;
// };


$(function () {

    // make the whole proposal area clickable (link needed only in an issue page)
    $('body').on('click', 'ul.prop-table.proposals', function () {
        var proposal_link = $(this).find('a');
        if (proposal_link.length) {
            window.location = proposal_link.attr('href');
        }
    });

    // Force links in user content to open in a new window
    $('body').on('click', '.userhtml a', function (event) {
        window.open($(this).prop('href'));
        return false;
    });

    $("body").on('click', 'a,button', function () {

        if ($(this).data('rel') != 'form') {
            return;
        }

        var url = $(this).attr('href') || $(this).data('url');
        var modal = $('#modal-form');

        var origin = $(this);

        $.get(url,function (html) {
            modal.html(html);
            initForm(modal, url, origin);
            modal.modal({backdrop: 'static'}).one('hidden.bs.modal', function () {
                $(this).removeData('bs.modal').empty();
            });
        }).fail(function () {
                alert('Server Error, please reload page.');
            });

        return false;
    });

    // Quick submit of new issue (Title only)
    $("body").on('click', '#quick-issue-add', function (e) {
        e.preventDefault();

        if ($('#quick-issue-title').val() == '') {
            return;
        }

        var url = $('#quick-issue-form').attr('action');
        var origin = $(this);
        var form = $('#quick-issue-form');

        form.ajaxForm({

            url: url,

            success: function (resp) {
                if (resp) {

                    var appendTo = $(origin).data('append-to');
                    if (appendTo) {
                        $(appendTo).append(resp);
                        return;
                    }

                    var replace = $(origin).data('replace');
                    if (replace) {
                        $(replace).html(resp);
                        $('body').trigger('ocd.updated');
                        return;
                    }

                    if (resp == '-') {
                        window.history.back();
                    } else {
                        window.location.href = resp;
                    }
                } else {
                    window.location.reload();
                }
            },

            error: function (resp) {
                if (resp.status == 403) {
                    $('#quick-issue-form .input-group').addClass('has-error');
                    $('#quick-issue-error').html(gettext('Field cannot be empty'));
                } else {
                    alert('Server Error! please try again or reload the page.');
                }
            }
        });
        $('#quick-issue-form').submit();
    });

    // Quick submit of new proposal (Title only)
    $("body").on('click', '#quick-proposal-add', function (e) {
        e.preventDefault();

        if ($('#quick-proposal-title').val() == '') {
            return;
        }

        var url = $('#quick-proposal-form').attr('action');
        var origin = $(this);
        var form = $('#quick-proposal-form');

        form.ajaxForm({

            url: url,

            success: function (resp) {
                if (resp) {

                    var appendTo = $(origin).data('append-to');
                    if (appendTo) {
                        $(appendTo).append(resp);
                        return;
                    }

                    var replace = $(origin).data('replace');
                    if (replace) {
                        $(replace).html(resp);
                        $('body').trigger('ocd.updated');
                        return;
                    }

                    if (resp == '-') {
                        window.history.back();
                    } else {
                        window.location.href = resp;
                    }
                } else {
                    window.location.reload();
                }
            },

            error: function (resp) {
                if (resp.status == 403) {
                    $('#quick-proposal-form .input-group').addClass('has-error');
                    $('#quick-proposal-error').html(gettext('Field cannot be empty'));
                } else {
                    alert('Server Error! please try again or reload the page.');
                }
            }
        });
        $('#quick-proposal-form').submit();
    });

    if (navigator.userAgent.match('CriOS')) {
        $('body').addClass('ios-chrome');
    }

});


/**
 * Initializes an ajax form to allow refreshing on error and redirecting,
 * reloading, going back or calling a custom callback function on success.
 *
 * @param {jQuery} modal
 * @param {jQuery} origin optional. The original link clicked to
 */
function initForm(modal, url, origin) {

    var form = modal.find('form');
    tinymce.init({
        selector: 'form .htmlarea textarea',
        menubar: false,
        statusbar: false,
        height: 80,
        language: 'he_IL',
        directionality: 'rtl',
        plugins: [
            'link directionality'
        ],
        toolbar: 'bullist numlist outdent indent | bold italic underline | alignleft aligncenter alignright | link'
    });
    // form.enhanceHtml().ajaxForm({
    form.ajaxForm({

        url: url,

        beforeSubmit: function () {
            form.find('input[type="submit"]').prop('disabled', true);
            if (form.find('input[type="file"]').length > 0) {
                $('input#id_file').parent().find('span.loader').remove();
                $('input#id_file').parent().append($('span.loader:first').clone().show());
            }
        },

        success: function (resp) {
            if (resp) {

                var appendTo = $(origin).data('append-to');
                if (appendTo) {
                    $(appendTo).append(resp);
                    $(modal).modal('hide');
                    return;
                }

                var replace = $(origin).data('replace');
                if (replace) {
                    $(replace).html(resp);
                    $(modal).modal('hide');
                    $('body').trigger('ocd.updated');
                    return;
                }

                if (resp == '-') {
                    window.history.back();
                } else {
                    window.location.href = resp;
                }
            } else {
                window.location.reload();
            }
        },

        error: function (resp) {
            if (resp.status == 403) {
                var newEl = $(resp.responseText.trim());
                form.html(newEl.find('form').html());
            } else {
                alert('Server Error! please try again or reload the page.');
                form.find('input[type="submit"]').prop('disabled', false);
            }
        }
    });

}
