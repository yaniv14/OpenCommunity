"use strict";


// Add/Remove disable from submit button.
function addRemoveSubmitButton() {
    $("body").on("keyup", "#id_argument", function () {
        var textLength = $("#id_argument").val().length;
        if (textLength > 0) {
            $(".argument-modal-btn").attr("disabled", false);
        } else {
            $(".argument-modal-btn").attr("disabled", true);
        }
    });
}

// Ajax argument delete form submission.
function deleteArgument() {
    $(".delete-argument").on('click', function (e) {
        var formURL = $(this).attr("action");
        var postData = $(this).serializeArray();
        $.ajax({
            url: formURL,
            type: "POST",
            data: postData,
            success: function (data, textStatus, jqXHR) {
                window.location.reload();
//                $("tr[data-id='" + data + "']").remove();
            },
            error: function (jqXHR, textStatus, errorThrown) {
                console.log(errorThrown);
            }
        });
        e.preventDefault();
    });
};

// Ajax argument form submission.

function addArgument() {
    $("#argument-submit").on('click', function (e) {
        var formObj = $('#create-argument');
        var voteStatus = formObj.data("vote");
        var formURL = formObj.attr("action");
        var postData = formObj.serializeArray();
        $('#argumentModal').modal('hide');
        $.ajax({
            url: formURL,
            type: "POST",
            data: postData,
            success: function (data, textStatus, jqXHR) {
//                $("#create-argument").get(0).reset();
                $('#create-argument').remove();
                $(".argument-modal-btn").attr("disabled", "disabled");
                if (voteStatus == 'pro') {
                    $(".arguments-table.pro-table tbody").append(data);
                } else {
                    $(".arguments-table.con-table tbody").append(data);
                }
                deleteArgument();
//                upDownVote();
//                addRemoveSubmitButton();
            },
            error: function (jqXHR, textStatus, errorThrown) {
                $("#create-argument").get(0).reset();
                $(".argument-modal-btn").attr("disabled", "disabled");
                deleteArgument();
                upDownVote();
                addRemoveSubmitButton();
                console.log(errorThrown);
            }
        });
        e.preventDefault();
    });
};

// Edit argument

function editArgument() {
    $('#editArgumentModal').on('show.bs.modal', function (event) {
        var button = $(event.relatedTarget);
        var vote_id = button.parents('tr').data('id');
        $('#edit-argument').attr("data-id", vote_id);
        var url = button.data('url');
        var arg_value_url = button.data('valueurl');
        $('#edit-argument').attr('action', url);
        $.get(arg_value_url, function (data) {
            $('#edit_argument_text').val(data);
        });
    });
}

// Ajax update argument form submission.

function editArgumentSubmit() {
    $("#edit-argument-submit").on('click', function (e) {
        var formObj = $('#edit-argument');
        var voteId = formObj.data("id");
        var formURL = formObj.attr("action");
        var postData = formObj.serializeArray();
        $('#editArgumentModal').modal('hide');
        $.ajax({
            url: formURL,
            type: "POST",
            data: postData,
            success: function (data, textStatus, jqXHR) {
                $("#edit-argument").get(0).reset();
                $("tr[data-id='" + voteId + "'] .arg-desc").html(data);
            },
            error: function (jqXHR, textStatus, errorThrown) {
                $("#edit-argument").get(0).reset();
                console.log(errorThrown);
            }
        });
        e.preventDefault();
    });
}

// Argument Upvote/Downvote

function upDownVote() {
    $('.vote-up,.vote-down').on('click', function () {
        if ($(this).hasClass('disabled')) {
            return;
        }
        var VoteId = $(this).parents('tr').data('id');
        var VoteVal = $(this).data('vote-val');
        var VoteUrl = $(this).parent().data('url');
        var VoteSib = $(this).siblings('a');
        var VoteCount = $(this).siblings('.vote-count');
        if (VoteSib.hasClass('voted')) {
            VoteSib.removeClass('voted');
        }
        $(this).toggleClass('voted');
        $.post(VoteUrl, {val: VoteVal})
            .success(function (data) {
                VoteCount.text(data);
            });
    });
}
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
            unaccept: '1'
        }, function (data) {
            history.back();
        });
    }

    function do_vote(vote_url, vote_value, elem, is_board) {
        var params = {
            'val': vote_value
        };
        if (is_board) {
            params['board'] = 1;
        }
        return $.post(vote_url, params, function (data) {
            if (data['result'] == 'ok') {
                var btn_div = elem.closest('div.vote-btns');
                if (is_board) {
                    var current = $('.vote_marked');
                    if (current.length) {
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
        var vote_box = $(this).parents('.vote-btns').siblings('.vote_arguments');
        var vote_value = $(this).attr('id').substr(5);
        var target = $(this).attr('href');
        var is_board = $(this).closest('.vote-btns').attr('id') == 'board_vote_btns';
        var prop_item = $(this).parents('.issue_proposal_vote');
        var args_url = $('#proposal-detail .proposal').data('argument-url');
        if (!args_url) {
            args_url = $(this).parents('.issue_proposal_vote').data('argument-url');
        }
        do_vote(target, vote_value, $(this), is_board)
            .done(function(){
                if (vote_value === 'reset') {
                    // TODO: Get new arguments content without the current user votes.
                    //vote_box.html('');
                    //fixHeights();
                    //window.location.reload();
                    $.get(args_url, function (arg) {
                        vote_box.html(arg);
                        fixHeights();
                        addRemoveSubmitButton();
                        addArgument();
                        editArgument();
                        editArgumentSubmit();
                        upDownVote();
                    });
                } else {
                    prop_item.addClass('with_arguments');
                    $.get(args_url, function (arg) {
                        vote_box.html(arg);
                        addRemoveSubmitButton();
                        addArgument();
                        editArgument();
                        editArgumentSubmit();
                        upDownVote();
                    });
                }
            });
    });

    // Check content saved before reload.
//    window.onbeforeunload = function () {
//        if ($('#id_content').val()) {
//            return gettext("Comment unsaved.");
//        }
//    };

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
        }
        var issue_h = $('.proposal_right_column').outerHeight();
        var proposal_h = $('.proposal_left_column').outerHeight();
        if ((issue_h + 20) < proposal_h) {
            $('.proposal_right_column').outerHeight(proposal_h - 20);
            return;
        }
        if (issue_h > proposal_h) {
            $('.proposal_left_column').outerHeight(issue_h + 20);
            return;
        }

    };

    $('body').on('ocd.show', function () {
        fixHeights();
    });

    $(window).resize(function () {
        fixHeights();
    });

    // Enable/Disable argument modal button for empty field.

    addArgument();
    deleteArgument();
    editArgument();
    editArgumentSubmit();
    upDownVote();
    addRemoveSubmitButton();

});
