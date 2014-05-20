"use strict";

var issue_sort = '';

function sort_issues(by) {
    if (!by) {
        if (!$('#issues-order').length) {
            return;
        }
        by = $('#issues-order li.active a').attr('href');
    }
    $('#available li').hide();
    var sorted = issue_sort[by];
    $.each(sorted, function(idx, value) {
        var elem = $('#available li[data-issue="' + value + '"]');
        if (elem && elem.length == 1) {
            elem.detach();
            $('#available').append(elem);
        }
    });

    $('#available li').show();
}

$(function() {

    function reorderIssues(li, val, callback) {
        $('#agenda-container').addClass('loading');
        var l = $('#agenda li').map(function() {
            return $(this).data('issue');
        }).get();
        $.post('', {
            issues : l,
        }, function(data) {
            $('#agenda-container').removeClass('loading');
        }).fail(function() {
            alert('Server Error. Please refresh your browser and try again');
        });
    }

    function toggleIssue(li, val, callback) {
        $.post('', {
            issue : li.data('issue'),
            set : val
        }, function(data) {
            li.removeClass('loading');
        }).fail(function() {
            alert('Server Error. Please refresh your browser and try again');
        });
    }


    $('#agenda').on('click', '.addremove', function(ev) {
        //$(this).find('.icon-minus').removeClass('icon-minus').addClass('icon-plus');
        var el = $(this).parent().parent().detach();
        el.addClass('loading');
        $("#available").prepend(el);
        sort_issues();
        toggleIssue(el, 1);
        ev.preventDefault();
    }).sortable({
        'containment' : $('#agenda').parent().parent(),
        'opacity' : 0.6,
        cursorAt : {
            top : 25
        },
        handle : ".grab",
        update : function(event, ui) {
            reorderIssues();
        }
    }).removeClass('ui-corner-all').filter('li').removeClass('ui-corner-bottom');

    $('#available').on('click', '.addremove', function(ev) {
        var el = $(this).parent().parent().detach();
        el.addClass('loading');
        $("#agenda").append(el);
        sort_issues();
        toggleIssue(el, 0);
        ev.preventDefault();
    });

    $('#agenda').on('click', '.timer span', function() {
        $(this).hide();
        var v = $(this).data('strict');
        if (v == "") {
            v = '00:00';
        }
        $(this).parent().append($('<input type="number" step="5" min="0" max="360" class="x" value="' + v + '"/><button>' + Save + '</button>'));
    });

    $('#agenda').on('click', '.timer button', function() {
        var el = $(this).parent();
        var v = el.find('.x').val();
        el.find('input,button').detach();
        el.find('span').html('...').data('strict', v).show();
        $.post(el.data('url'), {
            length : v
        }, function(data) {
            el.find('span').text(data);
        });
    });

});
