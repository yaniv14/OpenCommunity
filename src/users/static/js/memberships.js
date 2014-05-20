$(function() {

    // Add invitation form
    $('#invite-form').ajaxForm({

        success: function(data) {
            var el = $(data.trim());
            $('label[for=id_email] .alert').remove();
            $("#invite-form").closest('li').before(el).parent();
            $("#invite-form").get(0).reset();
            el.hide().show('slow');
            el.find('button').button();
            el.closest('ul').prev().removeClass('hide');
            $("#invite-form #id_email").val("");
        },
        error: function(resp) {
                if (resp.status == 403 || resp.status == 400) {
					$('label[for=id_email] .alert').remove();
					$('label[for=id_email]').prepend(
					'<div class="alert alert-warning alert-dismissable" style="margin-top: 10px;">' +
				        '<button type="button" style="margin-right: 10px;" class="close" data-dismiss="alert" aria-hidden="true">×</button>' +
				        resp.responseText +
					'</div>');
                } else {
                    alert('Server Error! please try again or reload the page.');
                }
            }
        });


    // Delete invitation form
    $('#invitations').on('click', '.delete-invitation button', function() {
        var btn = $(this);
        var form = btn.closest('form');
        form.ajaxSubmit({
                            success: function(data) {
                                form.closest('li').hide('slow', function(){
                                    if($('li.list-group-item', $(this).parent()).length == 1) {
                                        $(this).parent().prev().addClass('hide');
                                    }  
                                    $(this).remove();
                                });
                            }
                        });
        return false;
    });

});
