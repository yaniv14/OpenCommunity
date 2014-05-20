$(function () {

    var TA = $("#add_member");
    var mem_list = $('ul#members-list');
    var selectedMembers = {};
    mem_list.find('li').each(function () {
        selectedMembers[$(this).data('uid')] = true;
    });

    var addMember = function (id, label) {
        $('#p_select input[value="' + id + '"]').prop('checked', true);
        if (!(id in selectedMembers)) {
            selectedMembers[id] = true;
            mem_list.append($(member_tpl.replace('#NAME#', label).replace('#ID#', id)));
        };
    };

    var delMember = function (id) {
        $("#recommended-members").find("[data-uid='" + id + "']").children('button').removeClass('disabled');
        $('#p_select input[value="' + id + '"]').prop('checked', false);
        delete selectedMembers[id];
    };

    $('.participant-title button').on('click', function () {
        $(".select-participants, .list-of-participants").toggle();
        $(".participants-body-list, .participants-body-form").toggle();
    });

    $('.board_select').on('change', 'li input', function () {
        var uid = $(this).val();
        var sel = $(this).is(':checked');
        $('#p_select input[value="' + uid + '"]').prop('checked', sel);
    });

    // user autocomplete setup
    var delete_text = gettext('Delete');
    var tpl = '<p>{{value}}</p>';
    var member_tpl = '<li class="list-group-item" data-uid="#ID#">' +
        '<div style="display: inline;line-height: 30px;">' +
        '#NAME#</div>' +
        '<button type="button" class="del_member pull-right btn btn-danger btn-sm">' +
        '<i class="fa fa-trash-o"></i> ' +
        delete_text +
        '</button></li>';
    var guest_tpl = '<li class="list-group-item" data-guest="#GUEST_RAW#">' +
        '<div style="display: inline;line-height: 30px;">' +
        '#G_DETAIL#</div>' +
        '<button type="button" class="pull-right btn btn-danger btn-sm del_guest">' +
        '<i class="fa fa-trash-o"></i> ' + delete_text + '</button></li>';

    TA.typeahead({
        prefetch: typeahead_url,
        cache: false,
        remote: typeahead_url + '&q=%QUERY',
        engine: Hogan,
        autoselect: true,
        highlight: true
        // template : tpl
    }).bind('typeahead:selected',function (_, data) {
            addMember(data.user__id, data.value);
            TA.typeahead('setQuery', '');
        }).css({'background-color': '#fff', 'direction': OCD.language == 'he' ? "rtl" : 'ltr'});

    TA.on('typeahead:selected',function (object, datum) {
        $(this).data('uid', datum['user__id']);
    });

    $('#recommended-members').on('click', '.add-rec-member', function () {
        var uid = $(this).parent().data('uid');
		var new_name = $(this).parent().find('div').text();
		addMember(uid, new_name);
        // $(this).parent().remove();
        $(this).addClass('disabled');
    });

    $('#members').on('click', 'button.del_member', function (ev) {
        var elem = $(this).closest('li');
        var uid = elem.data('uid');
        elem.remove();
        delMember(uid);
    });

// Hide and show add memeber button

    TA.on('input', function () {
        if ($(this).val() == "") {
            $('#add_member_btn').addClass('disabled');
        } else {
            $('#add_member_btn').removeClass('disabled');
        }
    });

    $('#guests').on('click', '#add_guest_btn', function () {
        var guest_name_inp = $('input#guest_name');
        var guest_email_inp = $('input#guest_email');

        // validate name
        if (guest_name_inp.val() == '') {
            guest_name_inp.focus().css('border-color', 'red');
            return;
        }
        else {
            guest_name_inp.css('border-color', '#ccc');
        }
        // validate guests fields
        if (!guest_email_inp.get(0).checkValidity()) {
            guest_email_inp.focus().css('border-color', 'red');
            return;
        }
        else {
            guest_email_inp.css('border-color', '#ccc');
        }

        var guest_details = guest_name_inp.val();
        if (guest_email_inp.val()) {
            guest_details += ' [' + guest_email_inp.val() + ']';
        }
        $('ul#guests-list').append($(guest_tpl.replace('#G_DETAIL#', guest_details)));
        var cur_guests = $('#id_upcoming_meeting_guests').text();
        var updated = (cur_guests.length == 0) ? guest_details
            : cur_guests + '\n' + guest_details;
        $('#id_upcoming_meeting_guests').text(updated);
        $('#guests input').val('');
    });

    $('#recommended-guests').on('click', '.add-rec-guest', function () {
        var guest_details = $(this).parent().find('div').text().replace(/[\n\r\t]/g, "");
        $('ul#guests-list').append($(guest_tpl.replace('#G_DETAIL#', guest_details)));
        var cur_guests = $('#id_upcoming_meeting_guests').text();
        var updated = (cur_guests.length == 0) ? guest_details
            : cur_guests + '\n' + guest_details;
        $('#id_upcoming_meeting_guests').text(updated);
        $(this).parent().remove();
        $('#guests h3').toggle($('#recommended-guests li').length);
    });

    $('#guests').on('click', 'button.del_guest', function (ev) {
        var elem = $(this).closest('li');
        var guest_txt = $(this).prev().text().replace(/[\t\n]/g, "");
        elem.remove();
        //var rgx = new RegExp('\s*' + guest_txt + '\s*\n*');
        var guests = $('#id_upcoming_meeting_guests').text();
        var idx = guests.indexOf(guest_txt);
        var end_idx = guests.indexOf('\n', idx);
        var text_without = guests.slice(0, idx);
        if (end_idx != -1) {
            text_without += guests.slice(end_idx + 1);
        }
        $('#id_upcoming_meeting_guests').text(text_without.replace('\n\n', '\n'));
    });

    $("form :input").on("keypress", function(e) {
        return e.keyCode != 13;
    });

}); 
