$(function () {
    var $deleteCommentButton;
    // use modal dialog when deleting a blog in delete view
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
    $("#js-content").on("click", ".js-delete-blog", loadForm);
    $("#createbtn").on("click", ".js-create-tag", loadForm);

    // search for a blog in the blog list and user profile view
    $("#search-input").keyup(function() {
        var input, filter, titles, ul, a, i;
        input = $("#search-input");
        filter = input.val().toUpperCase();
        a = $("#blog-search a");
        for (i=0; i<a.length; ++i){
            if (a[i].innerHTML.toUpperCase().indexOf(filter) > -1) {
                a[i].style.display = "block";
                if($("#blog-search > div").hasClass("js-hide-div")){
                    a[i].parentElement.parentElement.parentElement.style.display = "block";
                }
            } else {
                a[i].style.display = "none";
                if($("#blog-search > div").hasClass("js-hide-div")){
                    a[i].parentElement.parentElement.parentElement.style.display = "none";
                }
            }
        }
    });

    // image cropper
    $("#id_profile_img").change(function () {
        var file = $(this).val().toLowerCase();
        var ext = file.substring(file.lastIndexOf('.') + 1);
        if($.inArray(ext, ['jpg', 'jpeg', 'png', 'bmp']) == -1){
            alert("Please Upload a valid image with the following formats (.jpg, .jpeg, .png, .bmp)");
        }
        else{
            if (this.files && this.files[0]) {
                var reader = new FileReader();
                reader.onload = function (e) {
                    $("#image").attr("src", e.target.result);
                    $("#modalCrop").modal("show");
                }
                reader.readAsDataURL(this.files[0]);
            }
        }
    });

    // HANDLE THE CROPPER BOX
    var $image = $("#image");
    var cropBoxData;
    var canvasData;
    $("#modalCrop").on("shown.bs.modal", function () {
        $image.cropper({
            viewMode: 1,
            aspectRatio: 1/1,
            minCropBoxWidth: 200,
            minCropBoxHeight: 200,
            ready: function () {
                $image.cropper("setCanvasData", canvasData);
                $image.cropper("setCropBoxData", cropBoxData);
            }
        });
    }).on("hidden.bs.modal", function () {
        cropBoxData = $image.cropper("getCropBoxData");
        canvasData = $image.cropper("getCanvasData");
        $image.cropper("destroy");
    });

    // Enable zoom in button
    $(".js-zoom-in").click(function () {
        $image.cropper("zoom", 0.1);
    });

    // Enable zoom out button
    $(".js-zoom-out").click(function () {
        $image.cropper("zoom", -0.1);
    });

    /* SCRIPT TO COLLECT THE DATA AND POST TO THE SERVER */
    $(".js-crop-and-upload").click(function () {
        var cropData = $image.cropper("getData");
        $("#id_x").val(cropData["x"]);
        $("#id_y").val(cropData["y"]);
        $("#id_height").val(cropData["height"]);
        $("#id_width").val(cropData["width"]);
        $("#formUpload").submit();
    });

    var scrollLink = $('.scroll');
    // Smooth scrolling
    scrollLink.click(function(e) {
        e.preventDefault();
        $('body,html').animate({
        scrollTop: $(this.hash).offset().top-68 //navbar height
    }, 900 );
    });

    // comment system
    var replyLink = function(e){
        e.preventDefault();
        $(this).parents().eq(3).next(".js-replies").toggleClass("d-none");
    };

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
                if($formButton.text() === 'comment'){
                    var $comment = $(".js-parent-comment");
                    if($comment.length > 0){
                        $(data).insertBefore($comment[0]);
                    }else{
                        var $mainDiv = $(".js-main-comment");
                        $mainDiv.append(data);
                    }
                }else{
                    $(data).insertBefore($form);
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
                commentCount(1);
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
        e.preventDefault();
        var commentContent = $(this).parents().eq(2)[0];
        commentBeforeEdit = commentContent;
        var $thisURL = $(this).attr('href');
        $.ajax({
            method: 'GET',
            url: $thisURL,
            success: function updateComment(data, textStatus, jqXHR){
                $(commentContent).replaceWith(data);
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
                    var rNum = Number($replyNumber.text())-1;
                    $replyNumber.replaceWith('<span class="js-reply-number text-dark">'+rNum+'</span>');
                    if(rNum>1){
                        $reply.replaceWith('<a class="js-reply-link ml-1" href="#">Replies</a>');
                    }else{
                        $reply.replaceWith('<a class="js-reply-link ml-1" href="#">Reply</a>');
                    }
                }

                // data.count is the children of parent comment
                // and 0 if the deleted comment is a child
                commentCount(-(data.count+1));
            },
            error: function handleFormError(jqXHR, textStatus, errorThrown){
                console.log(jqXHR);
                console.log(textStatus);
                console.log(errorThrown);
            },
        });
    }

    // $(document).on("submit", '.js-comment-form', commentFormSubmit);
    // $(document).on("click", ".js-reply-link", replyLink);
    // $(document).on("input keyup keypress focus", ".js-comment-input", commentInput);
    // $(document).on("click", ".js-comment-edit", editComment);
    // $(document).on("submit", ".js-comment-edit-form", commentEditFormSubmit);
    // $(document).on("click", ".js-comment-cancel", cancelEdit);
    // $(document).on("click", ".js-comment-delete", loadForm);
    // $(document).on("submit", ".js-comment-delete-form", deleteComment);


    // like button
    likeSubmit = function(e){
        e.preventDefault();
        var $likeLink = $(this);
        var $thisURL = $likeLink.attr('href');
        $.ajax({
            method: "GET",
            url: $thisURL,
            success: function handleLinkSuccess(data, textStatus, jqXHR){
                var $likeNumSpan = $(".js-like-number");
                $likeNumSpan.replaceWith('<span class="js-like-number mr-2">'+data.likes+'</span>');
                $(".js-like-link > button").prop("disabled", true);
            },
            error: function handleFormError(jqXHR, textStatus, errorThrown){

            },
        });
    }
    $(document).on("click", ".js-like-link", likeSubmit);
    // search bar
    var i=!1;
    $(".js-search-field").blur(function(){
        i?($(".js-search-field").focus(), i = !1):$(".s-btn").addClass("d-none");
    });
    $(".js-search-field").focus(function(){
        $(".s-btn").removeClass("d-none");
    });
    $(".s-btn").on("mousedown", function(){
        i = !0;
    });

    var prevScroll = $(this).scrollTop();
    $(window).scroll(function(){
        var currentScroll = $(this).scrollTop();
        var authorCard = $(".js-author-card").height()+48*2;
        // hide navbar in blog detail template only
        if(authorCard){
            if(prevScroll>currentScroll){
                $(".js-navbar").addClass("fixed-top");
            }else if(prevScroll<currentScroll && currentScroll>authorCard){
                $(".js-navbar").removeClass("fixed-top");
            }
            prevScroll = currentScroll;
        }

    });

    $(window).on("click touchend touch touchstart", function(e){
        var navbar = $(".js-navbar")[0];
        if(e.target !== navbar && !navbar.contains(e.target)){
            $(".js-btn-toggler").addClass("collapsed");
            $("#navbarText").removeClass("show");
        }
    });


////////////////////////////////////////////////////////////////////////////////
    // tag input
    var $tagInput = $("#tag-input");
    var $tagList = $(".js-tag");
    var $tagEditor = $(".tag-editor");
    var $formItem = $(".form-item");
    var $tagItem = $(".js-tag li");
    var $tagEditorSpan = $(".tag-editor > span");
    var $option = $('#id_tag option');
    var $selected_option = $('#id_tag option:selected');

    function addTag(tagName){
        $tagEditorSpan.append('<span class="post-tag">'+tagName+
        '<span class="delete-tag" title="remove this tag"></span></span>');
    }
    function setInputWidth(){
        var tagInputWidth = $tagEditor.width() - $tagEditorSpan.width()-5;
        $tagInput.attr("style", "width: "+tagInputWidth+"px;");
    }

    // add focus to tag-editor div
    $tagInput.focus(function(){
        $(this).parent('div').addClass("div-focus");
    }).blur(function(){
        $(this).parent('div').removeClass("div-focus");
    });


    // show the hidden tag div (tags list)
    $tagInput.on("keyup keypress", function(){
        // set tag list width
        $tagList.attr("style", "width: "+$formItem.width()+"px;");
        if($(this).val().replace(/^\s+|\s+$/g, "").length === 0){
            $tagList.addClass("d-none");
            $(".js-invalid").attr("style", "display: none");
        }else{
            // show tags matching the input value
            var filter = $(this).val().toUpperCase();
            var bool = !1;
            // allow 5 tags only per blog
            if($tagEditorSpan.children().length < 5){
                for (var i=0; i<$tagItem.length; ++i){
                    if ($tagItem[i].innerHTML.toUpperCase().indexOf(filter) > -1){
                        bool = !0;
                        $tagItem[i].style.display = "block";
                    } else {
                        $tagItem[i].style.display = "none";
                    }
                }
            }else{
                $(".js-invalid").attr("style", "display: block");
            }
            if(bool){
                $tagList.removeClass("d-none");
            }else{
                $tagList.addClass("d-none");
            }
        }
    });

    // show selected option in the tag-editor when refreshing or editing
    $selected_option.each(function(){
        addTag($(this).text());
        setInputWidth();
        $tagInput.attr("placeholder", "");
    });

    // add the tag to tag-editor
    $tagItem.on("click touchend", function(e){
        addTag(e.target.innerHTML);
        setInputWidth();
        $tagList.addClass("d-none");
        $tagInput.val("");

        // select corresponding choice in the hidden field
        $option.each(function(){
            if ($(this).text() === e.target.innerHTML){
                $(this).prop("selected", true);
            }
        });
        $tagInput.attr("placeholder", "");
        $tagInput.focus();
    });

    // delete tag from tag-editor
    $tagEditor.on("click touchend", ".delete-tag", function(e){
        var tagName = $(this).parent().text();
        var tagExist = !1;
        $(this).parent().remove();
        $tagInput.focus();
        $(".delete-tag").each(function(){
            if($(this).parent().text() === tagName){
                tagExist = !0;
            }
        });
        // check if deleted tag is duplicated
        if(!tagExist){
            $option.each(function(){
                if ($(this).text() === tagName){
                    $(this).prop("selected", false);
                }
            });
        }
        setInputWidth();
        if($(".delete-tag").length === 0){
            $tagInput.attr("placeholder", "At least one tag (e.g. Python, Django) Maximum 5");
        }

    });


    // resize blog panels to fit the viewport in blog views
    function resizeFun () {
        // blog panels
        var viewportHeight = window.innerHeight;
        var navbarHeight = $(".navbar").height();
        var create_btnHeight = $("#createbtn").height();
        var userHeight = $("#user").height();
        // socila links in home page
        $("#js-social-links").attr("style", "top: "+ viewportHeight/3);

        // 95 margins
        var leftcardHeight = viewportHeight - (navbarHeight + create_btnHeight + userHeight + 91);
        var rightcardHeight = viewportHeight - (navbarHeight + 16);

        $("#left-card").attr("style","height: "+leftcardHeight+"px;");
        $("#right-card").attr("style","height: "+rightcardHeight+"px;");
        // tag input and list
        setInputWidth();
        $tagList.attr("style", "width: "+$formItem.width()+"px;");
    };
    resizeFun();
    $(window).resize(resizeFun);

});
