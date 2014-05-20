"use strict";


$(function () {

    // disclaimer: this code is ugly.
    var sent = false;

    function setProposalStatus(id, value) {
        if (sent) {
            return;
        }
        sent = true;
        $(".accept-buttons,.unaccept").addClass('disabled');
        $.post('', {
            issue: id,
            accepted: value,
            unaccept: '1',
        }, function (data) {
            history.back();
        });
    }

    function do_vote(vote_url, vote_value, elem, is_board) {
        var params = {
          'val': vote_value
        };
        if(is_board) {
          params['board'] = '1';
        }
        $.post(vote_url, params, function (data) {
            if (data['result'] == 'ok') {
                var btn_div = elem.closest('div.vote-btns');
                if(is_board) {
                    var current = $('.vote_marked');
                    if(current.length) {
                        current.removeClass('vote_marked');
                    }
                    elem.addClass('vote_marked');
                    $('.board_vote').replaceWith(data['html']);
                }
                else {
                    btn_div.replaceWith(data['html']);
                }
            }
        });
    }


    $(".proposal-action").click(function (event) {
        event.preventDefault();
        var el = $(this).closest('.proposal');
        setProposalStatus(el.data('id'), $(this).val());
        return false;
    });

    $(".unaccept").click(function (event) {
        event.preventDefault();
        var el = $(this).closest('.proposal');
        setProposalStatus(el.data('id'), $(this).data('value'));
        return false;
    });

    $(".container").on("click", "a[id|='vote']", function (event) {
        event.preventDefault();
        var vote_value = $(this).attr('id').substr(5);
        var target = $(this).attr('href');
        var is_board = $(this).closest('.vote-btns').attr('id') == 'board_vote_btns';
        do_vote(target, vote_value, $(this), is_board);
    });

    window.onbeforeunload = function () {
        if ($('#id_content').val()) {
            return gettext("Comment unsaved.");
        }
    };

    $(".container").on("click", "a[id^='results']", function (event) {
        event.preventDefault();
        var target = $(this).attr('href');
        var id = $('.piechart').data('prop-id');
        $.get(target, function (data) {
            $('div.piechart').replaceWith(data);
            var pro = $('.piechart').data('pro');
            var con = $('.piechart').data('con');
            var total = $('.piechart').data('total');
            createChart(pro, con, total - (pro + con), id);
        });
    });

    var fixHeights = function () {
        $('.proposal_right_column,.proposal_left_column').css('height', 'auto');
        if (!$('.proposal_right_column').is(":visible")) {
            return;
        };
        var issue_h = $('.proposal_right_column').outerHeight();
        var proposal_h = $('.proposal_left_column').outerHeight();
        if ((issue_h + 20) < proposal_h) {
            $('.proposal_right_column').outerHeight(proposal_h - 20);
            return;
        };
        if (issue_h > proposal_h) {
            $('.proposal_left_column').outerHeight(issue_h + 20);
            return;
        };

    };

    $('body').on('ocd.show', function () {
        fixHeights();
    });

    $(window).resize(function () {
        fixHeights();
    });

});
