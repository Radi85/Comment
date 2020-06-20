$(function() {
    var $deleteCommentButton;
    var csrfToken = window.CSRF_TOKEN;

    $(".js-comment-input").val('');

    // use modal dialog when deleting a item
    var loadForm = function() {
        var btn = $(this);
        $deleteCommentButton = btn;
        $.ajax({
            url: btn.attr("data-url"),
            type: 'get',
            dataType: 'json',
            beforeSend: function() {
                $("#Modal .modal-content").html("");
                $("#Modal").modal("show");
            },
            success: function(data) {
                // comment per page
                if (btn.attr("name") === "delete-from-profile") {
                    $("#Modal .modal-content").html(data.html_form);
                    // redirect the user to his profile page instead of blog list
                    $("#modal-btn").attr("name", "delete-from-profile");
                } else {
                    $("#Modal .modal-content").html(data.html_form);
                }
            }
        });
    };

    // show and hide children comments
    var replyLink = function(e) {
        e.preventDefault();
        $(this).parents().eq(3).next(".js-replies").toggleClass("d-none");
    };

    // resize the input field according to typed text
    var commentInput = function() {
        var disabledButton = $(this).parent().parent().find(".js-comment-btn");
        // check if the input has an empty value
        if ($(this).val().replace(/^\s+|\s+$/g, "").length === 0) {
            $(this).attr("style", "height: 31px;")
            disabledButton.prop("disabled", true);
        } else {
            disabledButton.prop("disabled", false);
        }
        $(this).attr("style", "height: 31px;");
        $(this).attr("style", "height: " + this.scrollHeight + "px;");
    };

    function commentCount(num) {
        var $commentNumber = $(".js-comment-number");
        var result = Number($commentNumber.text()) + num;
        $commentNumber.replaceWith("<span class='js-comment-number'>" + result + "</span>");
    }

    // AJAX for create new comment
    var commentFormSubmit = function(e) {
        e.preventDefault();
        var $form = $(this);
        var $formButton = $form.find("button");
        var $thisURL = $form.attr('data-url') || window.location.href;
        var $formData = $form.serializeArray();
        // send button name and value to BE
        $formData.push({ name: $formButton.attr('name'), value: $formButton.text() });

        $.ajax({
            method: "POST",
            url: $thisURL,
            data: $formData,
            success: function handleFormSuccess(data) {
                // parent comment
                if ($formButton.data('type') === 'parent') {
                    // reload all comments only when posting parent comment
                    $("#comments").replaceWith(data);

                } else {
                    // child comment
                    $(data).insertBefore($form);
                    // update number of replies
                    var $reply = $form.parent().prev().find(".js-reply-link");
                    var $replyNumber = $form.parent().prev().find(".js-reply-number");
                    var rNum = Number($replyNumber.text()) + 1;
                    $replyNumber.replaceWith('<span class="js-reply-number text-dark">' + rNum + '</span>');
                    if (rNum > 1) {
                        $reply.replaceWith('<a class="js-reply-link ml-1" href="#">Replies</a>');
                    } else {
                        $reply.replaceWith('<a class="js-reply-link ml-1" href="#">Reply</a>');
                    }
                    commentCount(1);
                }

                // resize and clear input value
                $(".js-comment-input").attr("style", "height: 31px;");
                $(".js-comment-btn").prop("disabled", true);
                $(".js-comment-input").val('');

                // remove pagination query when posting a new comment
                var uri = window.location.toString();
                if (uri.indexOf("?") > 0) {
                    var clean_uri = uri.substring(0, uri.indexOf("?"));
                    window.history.replaceState({}, document.title, clean_uri);
                }
            },
            error: function handleFormError(jqXHR, textStatus, errorThrown) {
                alert("Unable to post your comment!, please try again");
            },
        });
    };

    var commentBeforeEdit;
    var editComment = function(e) {
        // open a new form to edit the comment
        e.preventDefault();
        var commentContent = $(this).parents().eq(2)[0];
        commentBeforeEdit = commentContent; // store old comment
        var $thisURL = $(this).attr('href');
        $.ajax({
            method: 'GET',
            url: $thisURL,
            success: function updateComment(data, textStatus, jqXHR) {
                $(commentContent).replaceWith(data);
                // set the focus on the end of text
                var num = $(".js-comment-edit-form > textarea").val();
                $(".js-comment-edit-form > textarea").focus().val('').val(num);
            },
            error: function handleFormError(jqXHR, textStatus, errorThrown) {
                alert("you can't edit this comment");
            },
        });
    }

    var cancelEdit = function(e) {
        e.preventDefault();
        var editContent = $(this).parents().eq(3)[0];
        $(editContent).replaceWith(commentBeforeEdit);
    }

    var commentEditFormSubmit = function(e) {
        e.preventDefault();
        var $form = $(this);
        var $formButton = $form.find("button");
        var $formData = $form.serialize() + '&' + encodeURI($formButton.attr('name')) +
            '=' + encodeURI($formButton.text());
        var $thisURL = $(this).attr('data-url');
        $.ajax({
            method: 'POST',
            url: $thisURL,
            data: $formData,
            success: function submitUpdateComment(data, textStatus, jqXHR) {
                $form.parent().replaceWith(data);
            },
            error: function handleFormError(jqXHR, textStatus, errorThrown) {
                alert("Modification didn't take effect!, please try again");
            },
        });
    }

    var deleteComment = function(e) {
        e.preventDefault();
        var hasParent, paginate, comment_per_page;
        var $form = $(this);
        var $parentComment = $deleteCommentButton.parents().eq(4);
        var $reply = $deleteCommentButton.parents().eq(6).find(".js-reply-link");
        var $replyNumber = $deleteCommentButton.parents().eq(6).find(".js-reply-number");
        var $formData = $form.serializeArray();
        var $thisURL = $form.attr("data-url");

        // get the current page number and send it to pagination func
        var currentURL = window.location.href.split("=")[1];
        pageNumber = parseInt(currentURL, 10);

        // retrieve the comment status parent or child
        $.each($formData, function(i, field) {
            if (field.name === "has_parent") hasParent = field.value === "True";
        });

        // send page number to BE
        $formData.push({ name: 'page', value: pageNumber });

        $.ajax({
            method: "POST",
            url: $thisURL,
            data: $formData,
            success: function deleteCommentDone(data, textStatus, jqXHR) {
                $("#Modal").modal("hide");
                $parentComment.remove();
                var $parentCommentArr = $(".js-parent-comment");
                if (hasParent) {
                    // update replies count if a child was deleted
                    var rNum = Number($replyNumber.text()) - 1;
                    $replyNumber.replaceWith('<span class="js-reply-number text-dark">' + rNum + '</span>');
                    if (rNum > 1) {
                        $reply.replaceWith('<a class="js-reply-link ml-1" href="#">Replies</a>');
                    } else {
                        $reply.replaceWith('<a class="js-reply-link ml-1" href="#">Reply</a>');
                    }
                    // update total count of comments
                    commentCount(-1);
                } else {
                    // reload all comments only when deleting parent comment
                    $("#comments").replaceWith(data);
                    // clear BS classes and attr from body tag
                    $("body").removeClass("modal-open");
                    $("body").removeAttr("class");
                    $("body").removeAttr("style");
                    $(".modal-backdrop").remove();
                }
            },
            error: function handleFormError(jqXHR, textStatus, errorThrown) {
                alert("Unable to delete your comment!, please try again");
            },
        });
    };

    /**
     * Returns whether a classList contains a particular class or not.
     * @param {Array} classList - the array of classes to be compared.
     * @param {string} container - the class to be verified, default='user-has-not-reacted'.
     */
    var containsClass = function(classList, container = 'user-has-not-reacted') {
        if (classList.contains(container)) return true;
        return false;
    }

    /**
     * Changes/removes class to fill the reacted element.
     * @param {object} element - the DOM element that needs to be toggled.
     * @param {string} addClass -  the class to be added when action is 'add'.
     * @param {string} removeClass -  the class to be removed when action is 'add'.
     * @param {string} action -  'add' or 'remove'.
     */
    var toggleClass = function(element, addClass, removeClass, action) {
        if (action == 'add') {
            element.classList.add(addClass);
            element.classList.remove(removeClass);
        } else {
            element.classList.remove(addClass);
            element.classList.add(removeClass);
        }
    }

    /**
     * Fill the target reaction element, removes color from the other reaction
     * if it were filled. 
     * @param {object} $parent - parent of the reaction element that has to be updated
     * @param {object} $targetReaction - the reaction element to be filled
     */
    var fillReaction = function($parent, targetReaction) {
        likeIcon = $parent.find('.reaction-like').eq(0)[0];
        dislikeIcon = $parent.find('.reaction-dislike').eq(0)[0];
        var isLikeEmpty = containsClass(likeIcon.classList);
        var isDislikeEmpty = containsClass(dislikeIcon.classList);
        var addClass = "user-has-reacted";
        var removeClass = "user-has-not-reacted";
        if (isLikeEmpty && isDislikeEmpty) {
            toggleClass(targetReaction, addClass, removeClass, action = 'add');
        } else {
            var currentReaction = (isLikeEmpty) ? dislikeIcon : likeIcon;
            toggleClass(currentReaction, addClass, removeClass, action = 'remove');
            if (targetReaction != currentReaction) {
                toggleClass(targetReaction, addClass, removeClass, action = 'add');
            }
        }
    };

    /**
     * Change reaction count for the element that the user reacted upon.
     * @param {object} $parent - the parent object containing the reactions.
     * @param {Number} likes - like count
     * @param {Number} dislikes - dislike count
     */
    var changeReactionCount = function($parent, likes, dislikes) {
        $parent.find('.js-like-number').eq(0)[0].textContent = likes;
        $parent.find('.js-dislike-number').eq(0)[0].textContent = dislikes;
    }

    /**
     * Handle everything related to comment reactions
     * Fill the appropriate reaction icon
     * Update the count of reactions
     * @param {any} e - event which was triggered. 
     */
    var commentReact = function(e) {
        e.preventDefault();
        var $element = $(this);
        var targetReaction = $element.find('.comment-reaction-icon').eq(0)[0];
        var $parentReactionEle = $element.parent();
        var $thisURL = $element.attr('href');
        $.ajax({
            headers: { 'X-CSRFToken': csrfToken },
            method: "POST",
            url: $thisURL,
            dataType: 'json',
            success: function commentReactionDone(data, textStatus, jqXHR) {
                var status = data['status'];
                if (status === 0) {
                    fillReaction($parentReactionEle, targetReaction);
                    changeReactionCount($parentReactionEle, data['likes'], data['dislikes']);
                }
            },
            error: function handleFormError(jqXHR, textStatus, errorThrown) {
                alert("Reaction couldn't be processed!, please try again");
            },
        });
    };

    /**
     * Create a temporary div, append it to the div'#response', fix it to the top and fade it.
     * @param {string} responseEle - The DOM element to be used for displaying in the response.
     * @param {int} status - an integer based upon the response received for AJAX request.
     * (-1->'error'|0->'success'| 1->'warning')
     * @param {string} msg - a string depicting the message to be displayed in the response. 
     * @param {int} time - time after which the response fades away
     */
    function createResponse(responseEle, status, msg, time = 5000) {
        switch (status) {
            case -1:
                status = "danger";
                break;
            case 0:
                status = "success";
                break;
            case 1:
                status = "warning";
        }
        var cls = 'h6 alert alert-' + status;
        var temp = $('<div/>')
            .addClass(cls)
            .html(msg);
        responseEle.prepend(temp[0]);
        fixToTop(temp);
        temp.fadeIn(time);
        temp.fadeOut(2 * time);
        setTimeout(function() {
            temp.remove();
        }, 2 * time + 10);
    }
    /**
     * Fixes an element to the top of the viewport.
     * @param {object} div - element that is to be fixed at the top of the viewport. 
     */
    function fixToTop(div) {
        var top = 200;
        var isfixed = div.css('position') == 'fixed';
        if (div.scrollTop() > top && !isfixed)
            div.css({ 'position': 'fixed', 'top': '0px' });
        if (div.scrollTop < top && isfixed)
            div.css({ 'position': 'static', 'top': '0px' });
    }

    /**
     * Perform an AJAX request to the flag API and handle response.
     * @param {object} $flag - the parent DOM element that contains flag. 
     * @param {string} action - 'create'/'delete'.
     * @param {string} reason - the value of the reason for flagging, default=null.
     * @param {string} info - any extra information to be passed when flagging, default=null.
     */
    var sendFlag = function($flag, action, reason = null, info = null) {
        var data = {
            'reason': reason,
            'info': info,
            'action': action
        };
        var url = $flag.attr('data-url');
        var $modal = $flag.find('.flag-modal');
        $.ajax({
            headers: { 'X-CSRFToken': csrfToken },
            method: "POST",
            url: url,
            data: data,
            dataType: 'json',
            success: function commentFlagDone(data, textStatus, jqXHR) {
                var addClass = 'user-has-flagged';
                var removeClass = 'user-has-not-flagged';
                var flagIcon = $flag.find('.comment-flag-icon').eq(0)[0];
                if (data.flag === 1) {
                    toggleClass(flagIcon, addClass, removeClass, action = 'add');
                } else {
                    toggleClass(flagIcon, addClass, removeClass, action = 'remove')
                }
            },
            complete: function closeFlagModal(data) {
                $modal.modal('hide');
                if (data) {
                    data = data.responseJSON;
                    createResponse($flag.closest('.js-parent-comment')[0], data.status, data.msg);
                }
            },
            error: function handleFormError(jqXHR, textStatus, errorThrown) {
                alert("The flag action couldn't be processed!, please try again");
            }
        });
    };

    /**
     * Opens the modal form and handles everthing that occurs inside it.
     * @param {object} $flagEle - the parent DOM element that contains flag  
     */
    var handleFlagModal = function($flagEle) {
        var $modal = $flagEle.find('.flag-modal');
        $modal.modal('show');
        form = $modal.find('.flag-modal-form').eq(0)[0];
        var lastReason = form.querySelector('.flag-last-reason');
        var flagInfo = form.querySelector('textarea');
        form.onchange = function(e) {
            if (e.target === lastReason) {
                flagInfo.required = true;
                flagInfo.style.display = "block";
            } else {
                flagInfo.style.display = "none";
            }
        };
        var submit = $modal.find('.flag-modal-submit').eq(0)[0];
        submit.onclick = function(e) {
            e.preventDefault();
            var choice = form.querySelector('input[name="reason"]:checked');
            if (choice) {
                var reason = choice.value;
                sendFlag($flagEle, 'create', reason, flagInfo.value);
            }
        }
    };

    /**
     * Create or remove a flag option on a comment.
     * @param {any} e - the event triggered this action. 
     */
    var commentFlag = function(e) {
        var $parent = $(this);
        var $flag = $parent.find('.comment-flag-icon').eq(0)[0];
        if (containsClass($flag.classList, container = 'user-has-not-flagged')) {
            handleFlagModal($parent);
        } else {
            sendFlag($parent, action = 'delete');
        }
    };

    const toggleText = function (event) {
        event.target.previousElementSibling.classList.toggle('d-none');
        if (event.target.previousElementSibling.classList.contains('d-none')) {
           event.target.innerHTML = "read more ...";
        } else {
           event.target.innerHTML = "read less";
        }
    };

    const toggleFlagState = function() {
        const $this = $(this);
        const url = $this.data('url');
        const state = $this.data('state');
        const data = {
            'state': state
        };
        $.ajax({
            headers: { 'X-CSRFToken': csrfToken },
            method: "POST",
            url: url,
            data: data,
            dataType: 'json',
            success: function (result) {
                if (result.state === 0) return;
                $this.parents().eq(2).addClass('flagged-comment');
                var title = '';
                if (state === 3) {
                    $this.find(">:first-child").toggleClass("flag-rejected");
                    title = $this.find(">:first-child").hasClass("flag-rejected") ? 'Flag rejected' : 'Reject the flag';
                    const $contentModifiedBtn = $this.next();
                    if (result.state === 3) {
                        $contentModifiedBtn.find(">:first-child").removeClass("flag-resolved");
                        $contentModifiedBtn.attr('title', 'Resolve the flag');
                        $this.parents().eq(2).removeClass('flagged-comment');
                    }
                } else if (state === 4) {
                    $this.find(">:first-child").toggleClass("flag-resolved");
                    title = $this.find(">:first-child").hasClass("flag-resolved") ? 'Flag resolved' : 'Resolve the flag';
                    const $rejectBtn = $this.prev();
                    if (result.state === 4) {
                        $rejectBtn.find(">:first-child").removeClass("flag-rejected");
                        $rejectBtn.attr('title', 'Reject the flag');
                        $this.parents().eq(2).removeClass('flagged-comment');
                    }
                }
                $this.attr('title', title);
            },
        });
    };

    $(document).on("submit", '.js-comment-form', commentFormSubmit);
    $(document).on("click", ".js-reply-link", replyLink);
    $(document).on("input keyup keypress focus", ".js-comment-input", commentInput);
    $(document).on("click", ".js-comment-edit", editComment);
    $(document).on("submit", ".js-comment-edit-form", commentEditFormSubmit);
    $(document).on("click", ".js-comment-cancel", cancelEdit);
    $(document).on("click", ".js-comment-delete", loadForm);
    $(document).on("submit", ".js-comment-delete-form", deleteComment);
    $(document).on("click", ".js-comment-reaction", commentReact);
    $(document).on("click", ".js-comment-flag", commentFlag);
    $(document).on("click", ".js-read-more-btn", toggleText);
    $(document).on("click", ".js-flag-reject", toggleFlagState);
    $(document).on("click", ".js-flag-resolve", toggleFlagState);

});
