"use strict";

/**
 * Toggles visibilty for titles with no "child" elements.
 */
function toggleTitles() {
    $('.filter-title').each(function () {
        $(this).toggle($(this).next().find('.filter.on').length > 0);
    });
}

function setHeight() {
    $('.issue_left_column').css('height', 'auto');
    if (!$('.issue_right_column').is(":visible")) {
        return;
    }
    var issues_h = $('.issue_right_column').outerHeight();
    var frame_h = $('.issue_left_column').outerHeight();
    var inner_h = $('.issue_left_column_inner').outerHeight();
    if ((inner_h > frame_h) || (issues_h > frame_h)) {
        $('.issue_left_column').outerHeight(Math.max(inner_h, issues_h) + 20);
    }
}

$(function () {

    var doFilter = function(el) {

        var root = el.closest('[data-filter]');
        root.find('li').removeClass('active');
        el.parent('li').addClass('active');
        el.closest('li.dropdown').addClass('active');
        if (el.data('show')) {
            $(root.data('filter')).hide().removeClass('on');
            $(el.data('show')).show().addClass('on');
        } else {
            $(root.data('filter')).show().addClass('on');
        }
        if (el.data('hide')) {
            $(el.data('hide')).hide().removeClass('on');
        }

        toggleTitles();
        setHeight();
    };

    var filters = {};
    $('[data-toggle=filter]').each(function() {
        filters[$(this).attr('href')] = $(this);
    });
    if (Object.keys(filters).length > 1) {

        var hash = '#' + window.location.hash.replace(/^#/,'');
        if (hash == '#') {
           window.location.hash = '#upcoming' in filters ? '#upcoming' : '#all';
        }

        $(window).bind('hashchange', function() {
            var hash = '#' + window.location.hash.replace(/^#/,'');
            if (hash in filters) {
                doFilter(filters[hash]);
            }
        }).trigger('hashchange');

    } else {
        $('.filter').addClass('on');
        $('body').on('ocd.updated', function () {
            $('.filter-subtitle').hide();
        });
        $('.filter-subtitle').hide();
        toggleTitles();
    }
    $('body').on('ocd.show', function () {
        setHeight();
    });

    $(window).resize(setHeight);

});
