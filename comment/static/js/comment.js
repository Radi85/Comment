$(function () {
    var $deleteCommentButton;
    // use modal dialog when deleting a item
    var loadForm = function () {
        var btn = $(this);
        $deleteCommentButton = btn;
        $.ajax({
            url: btn.attr("data-url"),
            type: 'get',
            dataType: 'json',
            beforeSend: function () {
                $("#Modal .modal-content").html("");
                $("#Modal").modal("show");
            },
            success: function (data) {
                if (btn.attr("name") === "delete-from-profile"){
                    $("#Modal .modal-content").html(data.html_form);
                // redirect the user to his profile page instead of blog list
                    $("#modal-btn").attr("name", "delete-from-profile");
                }else{
                    $("#Modal .modal-content").html(data.html_form);
                }
            }
        });
    };

    // show and hide children comments
    var replyLink = function(e){
        e.preventDefault();
        $(this).parents().eq(3).next(".js-replies").toggleClass("d-none");
    };

    // resize the input field according to typed text
    var commentInput = function(){
        var disabledButton = $(this).parent().next().find(".js-comment-btn");
        // check if the input has an empty value
        if($(this).val().replace(/^\s+|\s+$/g, "").length === 0){
            $(this).attr("style", "height: 31px;")
            disabledButton.prop("disabled", true);
        }else{
            disabledButton.prop("disabled", false);
        }
        $(this).attr("style", "height: 31px;");
        $(this).attr("style", "height: "+this.scrollHeight+ "px;");
    };

    function commentCount(num){
        var $commentNumber = $(".js-comment-number");
        var result = Number($commentNumber.text())+num;
        $commentNumber.replaceWith("<span class='js-comment-number'>"+result+"</span>");
    }

    // AJAX for create new comment
    var commentFormSubmit = function(e){
        e.preventDefault();
        var $form = $(this);
        var $formButton = $form.find("button");
        var $formData = $form.serialize() + '&' + encodeURI($formButton.attr('name'))
                        + '=' + encodeURI($formButton.text());
        var $thisURL = $form.attr('data-url') || window.location.href;
        $.ajax({
            method: "POST",
            url: $thisURL,
            data: $formData,
            success: function handleFormSuccess(data, textStatus, jqXHR){
                // parent comment
                if($formButton.text() === 'comment'){
                    var $comment = $(".js-parent-comment");
                    if($comment.length > 0){
                        $(data).insertBefore($comment[0]);
                    }else{
                        var $mainDiv = $(".js-main-comment");
                        $mainDiv.append(data);
                    }
                }else{
                    // child comment
                    $(data).insertBefore($form);
                    // update number of replies
                    var $reply = $form.parent().prev().find(".js-reply-link");
                    var $replyNumber = $form.parent().prev().find(".js-reply-number");
                    var rNum = Number($replyNumber.text())+1;
                    $replyNumber.replaceWith('<span class="js-reply-number text-dark">'+rNum+'</span>');
                    if(rNum>1){
                        $reply.replaceWith('<a class="js-reply-link ml-1" href="#">Replies</a>');
                    }else{
                        $reply.replaceWith('<a class="js-reply-link ml-1" href="#">Reply</a>');
                    }
                }
                // increase comment count after submission
                commentCount(1);
                // resize and clear input value
                $(".js-comment-input").attr("style", "height: 31px;");
                $(".js-comment-btn").prop("disabled", true);
                $(".js-comment-input").val('');
            },
            error: function handleFormError(jqXHR, textStatus, errorThrown){
                // console.log(jqXHR)
                // console.log(textStatus)
                // console.log(errorThrown)
            },
        });
    };

    var commentBeforeEdit;
    var editComment = function(e){
        // open a new form to edit the comment
        e.preventDefault();
        var commentContent = $(this).parents().eq(2)[0];
        commentBeforeEdit = commentContent; // store old comment
        var $thisURL = $(this).attr('href');
        $.ajax({
            method: 'GET',
            url: $thisURL,
            success: function updateComment(data, textStatus, jqXHR){
                $(commentContent).replaceWith(data);
                // set the focus on the end of text
                var num = $(".js-comment-edit-form > textarea").val();
                $(".js-comment-edit-form > textarea").focus().val('').val(num);
            },
            error: function handleFormError(jqXHR, textStatus, errorThrown){
                alert("you can't edit this comment");
            },
        });
    }

    var cancelEdit = function(e){
        e.preventDefault();
        var editContent = $(this).parents().eq(3)[0];
        $(editContent).replaceWith(commentBeforeEdit);
    }

    var commentEditFormSubmit = function(e){
        e.preventDefault();
        var $form = $(this);
        var $formButton = $form.find("button");
        var $formData = $form.serialize() + '&' + encodeURI($formButton.attr('name'))
                        + '=' + encodeURI($formButton.text());
        var $thisURL = $(this).attr('data-url');
        $.ajax({
            method: 'POST',
            url: $thisURL,
            data: $formData,
            success: function submitUpdateComment(data, textStatus, jqXHR){
                $form.parent().replaceWith(data);
            },
            error: function handleFormError(jqXHR, textStatus, errorThrown){
                alert("Modification didn't take effect!, please try again");
            },
        });
    }

    var deleteComment = function(e){
        e.preventDefault();
        var $form = $(this);
        var $parentComment = $deleteCommentButton.parents().eq(4);
        var $reply = $deleteCommentButton.parents().eq(6).find(".js-reply-link");
        var $replyNumber = $deleteCommentButton.parents().eq(6).find(".js-reply-number");
        var $formData = $form.serialize();
        var $thisURL = $form.attr("data-url");
        $.ajax({
            method: "POST",
            url: $thisURL,
            data: $formData,
            success: function deleteCommentDone(data, textStatus, jqXHR){
                $("#Modal").modal("hide");
                $parentComment.remove();
                if(data.hasParent){
                    // update replies count if a child was deleted
                    var rNum = Number($replyNumber.text())-1;
                    $replyNumber.replaceWith('<span class="js-reply-number text-dark">'+rNum+'</span>');
                    if(rNum>1){
                        $reply.replaceWith('<a class="js-reply-link ml-1" href="#">Replies</a>');
                    }else{
                        $reply.replaceWith('<a class="js-reply-link ml-1" href="#">Reply</a>');
                    }
                }
                // data.count is number of the children of parent comment
                // and it is 0 if the deleted comment is a child
                commentCount(-(data.count+1));
            },
            error: function handleFormError(jqXHR, textStatus, errorThrown){
                alert("Unable to delete your comment!, please try again");
            },
        });
    }

    $(document).on("submit", '.js-comment-form', commentFormSubmit);
    $(document).on("click", ".js-reply-link", replyLink);
    $(document).on("input keyup keypress focus", ".js-comment-input", commentInput);
    $(document).on("click", ".js-comment-edit", editComment);
    $(document).on("submit", ".js-comment-edit-form", commentEditFormSubmit);
    $(document).on("click", ".js-comment-cancel", cancelEdit);
    $(document).on("click", ".js-comment-delete", loadForm);
    $(document).on("submit", ".js-comment-delete-form", deleteComment);
});
