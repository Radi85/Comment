/*jslint browser: true */
/*global window */
/*jslint plusplus: true */
document.addEventListener('DOMContentLoaded', () => {
    'use strict';
    let currentDeleteCommentButton, commentBeforeEdit;
    let csrfToken = window.CSRF_TOKEN;
    let headers = {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrfToken,
        'Content-Type': 'application/x-www-form-urlencoded'
    };
    document.getElementsByClassName(".js-comment-input").value = '';

    let removeTargetElement = e => {
        let currentHeight = window.pageYOffset;
        window.location.replace("#");
        // slice off the remaining '#':
        if (typeof window.history.replaceState == 'function') {
            history.replaceState({}, '', window.location.href.slice(0, -1));
        }
            window.scrollTo(0, currentHeight);
        }

    let showModal = modalElement => {
        modalElement.style.display = 'block';
        setTimeout(() => {
          modalElement.classList.add('show-modal');
        }, 20);
    };

    let hideModal = modalElement => {
        modalElement.classList.remove('show-modal');
        modalElement.style.display = 'none';
    };

    // show and hide child comments
    let replyLink = replyLinkElement => {
        getNthParent(replyLinkElement, 4).nextElementSibling.classList.toggle('d-none')
    };

    // resize the input field according to typed text
    let commentInput = textarea => {
        let commentButton = getNthParent(textarea, 2).querySelector(".js-comment-btn");
        textarea.setAttribute("style", "height: 31px;");
        textarea.setAttribute("style", "height: " + textarea.scrollHeight + "px;");
        if (textarea.value.replace(/^\s+|\s+$/g, "").length === 0) {
            textarea.setAttribute("style", "height: 31px;");
            if (commentButton) {
               commentButton.setAttribute('disabled', 'disabled');
            }
        } else {
            if (commentButton) {
               commentButton.removeAttribute('disabled');
            }
        }

    };

    let commentCount = num => {
        let commentNumber = document.getElementsByClassName("js-comment-number")[0];
        commentNumber.textContent = Number(commentNumber.textContent) + num;
    };

    let serializeArray = form => {
        let arr = [];
        Array.prototype.slice.call(form.elements).forEach(field => {
            if (!field.name || field.disabled || ['file', 'reset', 'button'].indexOf(field.type) > -1) return;
            if (field.type === 'select-multiple') {
                Array.prototype.slice.call(field.options).forEach(option => {
                    if (!option.selected) return;
                    arr.push({
                        name: field.name,
                        value: option.value
                    });
                });
                return;
            }
            if (['checkbox', 'radio'].indexOf(field.type) > -1 && !field.checked) return;
            arr.push({
                name: field.name,
                value: field.value
            });
        });
        return arr;
    };

    let serializeObject = form => {
        let object = {};
        serializeArray(form).map(n => {
            object[n['name']] = n['value'];
        });
        return object;
    };

    let stringToDom = (data, selector) => {
        let commentDOM = new DOMParser().parseFromString(data, "text/html");
        return commentDOM.querySelector(selector);
    };

    let convertFormDataToURLQuery = formData => {
        return Object.keys(formData).map((key) => {
          return encodeURIComponent(key) + '=' + encodeURIComponent(formData[key]);
        }).join('&');
    };

    // create new comment
    let submitCommentCreateForm = form => {
        let formButton = form.querySelector("button");
        let url = form.getAttribute('data-url') || window.location.href;
        let formData = serializeObject(form);
        // this step is needed to append the form data to request.POST
        let formDataQuery = convertFormDataToURLQuery(formData);
        fetch(url, {
           method: 'POST',
            headers: headers,
            body: formDataQuery
        }).then(response => {
            if (response.status === 200) {
                return response.text();
            }
            else if (response.status === 400) {
                return response.json();
            }
            return Promise.reject(response);
        }).then(data => {
            if (data.type === 'error') {
                console.log(data);
                alert(data.detail);
                return;
            }
           // parent comment
            if (formButton.getAttribute('value') === 'parent') {
                // reload all comments only when posting parent comment
                document.getElementById("comments").outerHTML = data;
            } else {
                // child comment
                let childComment = stringToDom(data, '.js-child-comment');
                form.parentNode.insertBefore(childComment, form);
                // update number of replies
                let reply = form.parentElement.previousElementSibling.querySelector(".js-reply-link");
                let replyNumberElement = form.parentElement.previousElementSibling.querySelector(".js-reply-number");
                let replyNum = Number(replyNumberElement.innerText) + 1;
                replyNumberElement.textContent = replyNum.toString();
                if (replyNum > 1) {
                    reply.textContent = "Replies";
                } else {
                    reply.textContent = "Reply";
                }
                commentCount(1);
            }
            formButton.setAttribute('disabled', 'disabled');
            let elements = document.getElementsByClassName("js-comment-input");
            Array.prototype.forEach.call(elements, element => {
                element.setAttribute("style", "height: 31px;");
                element.value = '';
            });
            // remove pagination query when posting a new comment
            let uri = window.location.toString();
            if (uri.indexOf("?") > 0) {
                let clean_uri = uri.substring(0, uri.indexOf("?"));
                window.history.replaceState({}, document.title, clean_uri);
            }
        }).catch(error => {
            alert("Unable to post your comment!, please try again");
        });
    };

    let setCommentForEditMode = editButton => {
        let commentContent = getNthParent(editButton, 3);
        commentBeforeEdit = commentContent; // store old comment
        let url = editButton.getAttribute('href');
        fetch(url, {headers: headers}).then(response => {
            return response.text();
        }).then(data => {
            let editModeElement = stringToDom(data, '.js-comment-update-mode');
            commentContent.replaceWith(editModeElement);
            // set the focus on the end of text
            let value = document.querySelector(".js-comment-edit-form").querySelector('textarea').value;
            let textAreaElement = document.querySelector(".js-comment-edit-form").querySelector('textarea');
            textAreaElement.focus();
            textAreaElement.value = '';
            textAreaElement.value = value;
            textAreaElement.setAttribute("style", "height: " + textAreaElement.scrollHeight + "px;")
        }).catch(error => {
            alert("you can't edit this comment");
        });
    };

    let cancelEdit = cancelBtn => {
        getNthParent(cancelBtn, 4).replaceWith(commentBeforeEdit);
    };

    let submitEditCommentForm = form => {
        let formData = serializeObject(form);
        let url = form.getAttribute('data-url');

        let formDataQuery = convertFormDataToURLQuery(formData);
        fetch(url, {
           method: 'POST',
            headers: headers,
            body: formDataQuery
        }).then(response => {
            return response.text();
        }).then(data => {
           let updatedContentElement = stringToDom(data, '.js-updated-comment');
           form.parentElement.replaceWith(updatedContentElement);
        }).catch(error => {
           alert("Modification didn't take effect!, please try again");
        });
    };

    let getParents = element => {
        let parent = element.parentElement;
        let parents = [];
        let commentRootElement = document.getElementById('comments');
        while (parent !== commentRootElement) {
            let child = parent;
            parents.push(child);
            parent = child.parentElement;
        }
        return parents;
    };

    let getParentByClassName = (element, className) => {
        let parents = getParents(element);
        for (let i=0; i<parents.length; i++) {
            if (parents[i].classList.contains(className)){
                return parents[i];
            }
        }
        return null;
    };

    let getNthParent = (element, nth) => {
        let parents = getParents(element);
        if (parents.length >= nth){
            return parents[nth-1]
        }
    };

    // use modal dialog when deleting a item
    let loadForm = deleteBtn => {
        currentDeleteCommentButton = deleteBtn;
        let url = deleteBtn.getAttribute('data-url');
        fetch(url, {headers: headers}).then(response => {
            return response.json()
        }).then(data => {
            let modal = document.getElementById("Modal");
            showModal(modal);
            let modalContent = modal.querySelector('.comment-modal-content');
            modalContent.innerHTML = data.html_form;
        }).catch(error => {
            console.error(error);
        });
    };

    let submitDeleteCommentForm = form =>{
        let commentElement = getNthParent(currentDeleteCommentButton, 5);
        let formData = serializeObject(form);
        let url = form.getAttribute("data-url");

        // get the current page number and send it to pagination func
        let currentURL = window.location.href.split("=")[1];
        formData['page'] = parseInt(currentURL, 10);
        let isParent = formData.isParent === "True";

        let formDataQuery = convertFormDataToURLQuery(formData);
        fetch(url, {
           method: 'POST',
            headers: headers,
            body: formDataQuery
        }).then(response => {
            return response.text();
        }).then(data => {
            if (isParent) {
                document.getElementById("comments").outerHTML = data;
            }
            else {
                // update replies count if a child was deleted
                let replyNumberElement = getParentByClassName(commentElement, 'js-parent-comment').querySelector(".js-reply-number");
                let replyLinkElement = getParentByClassName(commentElement, 'js-parent-comment').querySelector(".js-reply-link");
                let replyNum = Number(replyNumberElement.textContent) - 1;
                replyNumberElement.textContent = replyNum.toString();

                if (replyNum > 1) {
                    replyLinkElement.textContent = "Replies";
                } else {
                    replyLinkElement.textContent = "Reply";
                }
                // update total count of comments
                commentCount(-1);
            }
            let modal = document.getElementById("Modal");
            hideModal(modal);
            commentElement.remove();

        }).catch(error => {
            alert("Unable to delete your comment!, please try again");
        });
    };

    let hasClass = (classList, container = 'user-has-not-reacted') => {
        return !!classList.contains(container);
    };

    let toggleClass = (element, addClass, removeClass, action) => {
        if (action === 'add') {
            element.classList.add(addClass);
            element.classList.remove(removeClass);
        } else {
            element.classList.remove(addClass);
            element.classList.add(removeClass);
        }
    };

    let fillReaction = (parent, targetReaction) => {
        let likeIcon = parent.querySelector('.reaction-like');
        let dislikeIcon = parent.querySelector('.reaction-dislike');
        let isLikeEmpty = hasClass(likeIcon.classList);
        let isDislikeEmpty = hasClass(dislikeIcon.classList);
        let addClass = "user-has-reacted";
        let removeClass = "user-has-not-reacted";
        if (isLikeEmpty && isDislikeEmpty) {
            toggleClass(targetReaction, addClass, removeClass, 'add');
        } else {
            let currentReaction = (isLikeEmpty) ? dislikeIcon : likeIcon;
            toggleClass(currentReaction, addClass, removeClass, 'remove');
            if (targetReaction !== currentReaction) {
                toggleClass(targetReaction, addClass, removeClass, 'add');
            }
        }
    };

    let changeReactionCount = (parent, likes, dislikes) => {
        parent.querySelector('.js-like-number').textContent = likes;
        parent.querySelector('.js-dislike-number').textContent = dislikes;
    };

    let submitReaction = reactionButton => {
        let targetReaction = reactionButton.querySelector('.comment-reaction-icon');
        let parentReactionEle = reactionButton.parentElement;
        let url = reactionButton.getAttribute('href');
        fetch(url, {
           method: 'POST',
            headers: headers
           }).then(response => {
                return response.json();
            }).then(data => {
                let status = data.status;
                if (status === 0) {
                    fillReaction(parentReactionEle, targetReaction);
                    changeReactionCount(parentReactionEle, data.likes, data.dislikes);
                }
            }).catch(error => {
                alert("Reaction couldn't be processed!, please try again");
            });
        };

    let fadeOut = (element, duration) => {
      let interval = 10;//ms
        let opacity = 1.0;
        let targetOpacity = 0.0;
        let timer = setInterval(() => {
            if (opacity <= targetOpacity) {
                opacity = targetOpacity;
                clearInterval(timer);
            }
            element.style.opacity = opacity;
            opacity -= 1.0/((1000/interval)*duration);
        }, interval);
    };

    let fadeIn = (element, duration) => {
        let interval = 10;//ms
        let opacity = 0.0;
        let targetOpacity = 1.0;
        let timer = setInterval(() => {
            if (opacity >= targetOpacity) {
                opacity = targetOpacity;
                clearInterval(timer);
            }
            element.style.opacity = opacity;
            opacity += 1.0/((1000/interval)*duration);
        }, interval);
    };

    let createInfoElement = (responseEle, status, msg, duration = 2) => {
        switch (status) {
            case -1:
                status = "danger";
                break;
            case 0:
                status = "success";
                break;
            case 1:
                status = "warning";
                break;
        }
        let cls = 'alert-' + status;
        let temp = document.createElement('div');
        temp.classList.add('h6');
        temp.classList.add('alert');
        temp.classList.add(cls);
        temp.innerHTML = msg;
        responseEle.prepend(temp);
        fixToTop(temp);
        fadeIn(temp, duration );
        setTimeout(() =>{
          fadeOut(temp, duration);
        }, duration * 1500);

        setTimeout(() => {
            temp.remove();
        }, 2500 * duration);
    };

     let fixToTop = div => {
        let top = 200;
        let isFixed = div.style.position === 'fixed';
        if (div.scrollTop > top && !isFixed){
           div.setAttribute('style', "{'position': 'fixed', 'top': '0px'}");
        }
        if (div.scrollTop < top && isFixed) {
           div.setAttribute('style', "{'position': 'static', 'top': '0px'}");
        }

    };

    let submitFlagForm = (flagButton, action, reason=null, info=null) => {
        let formData = {
            'action': action
        };
        if (reason){
            formData['reason'] = reason
        }
        if (info){
            formData['info'] = info
        }
        let url = flagButton.getAttribute('data-url');

        let formDataQuery = convertFormDataToURLQuery(formData);
        fetch(url, {
           method: 'POST',
            headers: headers,
            body: formDataQuery
        }).then(response => {
            return response.json();
        }).then(data => {
            let addClass = 'user-has-flagged';
            let removeClass = 'user-has-not-flagged';
            let flagIcon = flagButton.querySelector('.comment-flag-icon');
            if (data.flag === 1) {
                toggleClass(flagIcon, addClass, removeClass, action = 'add');
            } else {
                toggleClass(flagIcon, addClass, removeClass, action = 'remove')
            }
            let modal = document.getElementById('flagModal');
            hideModal(modal);
            if (data) {
                createInfoElement(flagButton.closest('.js-parent-comment'), data.status, data.msg);
            }
        }).catch(error => {
            alert("Reaction couldn't be processed!, please try again");
        });
    };

    let handleFlagModal = flagButton => {
        let modal = document.getElementById('flagModal');
        showModal(modal);
        document.getElementById('flagModal').querySelector('textarea').value = '';
        let form = modal.querySelector('.flag-modal-form');
        let lastReason = form.querySelector('.flag-last-reason');
        let flagInfo = form.querySelector('textarea');
        flagInfo.style.display = "none";
        let elements = document.querySelectorAll('[name=reason]:first-child');
        elements[0].checked = true;
        form.onchange = e => {
            if (e.target === lastReason) {
                flagInfo.required = true;
                flagInfo.style.display = "block";
            }
            elements.forEach(element => {
                if (e.target === element && element !== lastReason) {
                    flagInfo.style.display = "none";
                }
            });
        };
        let submit = modal.querySelector('.flag-modal-submit');
        submit.onclick = e => {
            e.preventDefault();
            let choice = form.querySelector('input[name="reason"]:checked');
            let reason = choice.value;
            submitFlagForm(flagButton, 'create', reason, flagInfo.value);
        };
    };

    let setFlag = flagButton => {
        let flag = flagButton.querySelector('.comment-flag-icon');
        if (hasClass(flag.classList, 'user-has-not-flagged')) {
            handleFlagModal(flagButton);
        } else {
            submitFlagForm(flagButton, 'delete');
        }
    };

    const toggleText = readMoreButton => {
        readMoreButton.previousElementSibling.classList.toggle('d-none');
        if (readMoreButton.previousElementSibling.classList.contains('d-none')) {
           readMoreButton.innerHTML = "read more ...";
        } else {
           readMoreButton.innerHTML = "read less";
        }
    };

    const toggleFlagState = changeStateButton => {
        const url = changeStateButton.getAttribute('data-url');
        const state = parseInt(changeStateButton.getAttribute('data-state'));
        const formData = {
            'state': state
        };

        let formDataQuery = convertFormDataToURLQuery(formData);
        fetch(url, {
           method: 'POST',
            headers: headers,
            body: formDataQuery
        }).then(response => {
            return response.json();
        }).then(data => {
            if (data.state === 0) {
                return;
            }
            let commentBodyElement = getNthParent(changeStateButton, 3);
            commentBodyElement.classList.add('flagged-comment');
            let title = '';
            if (state === 3) {
                changeStateButton.firstElementChild.classList.toggle("flag-rejected");
                title = changeStateButton.firstElementChild.classList.contains("flag-rejected")
                    ? 'Flag rejected'
                    : 'Reject the flag';
                const contentModifiedBtn = changeStateButton.parentElement.querySelector('.js-flag-resolve');
                if (data.state === 3) {
                    if (contentModifiedBtn) {
                       contentModifiedBtn.firstElementChild.classList.remove("flag-resolved");
                        contentModifiedBtn.setAttribute('title', 'Resolve the flag');
                    }
                    commentBodyElement.classList.remove('flagged-comment');
                }
            } else if (state === 4) {
                changeStateButton.firstElementChild.classList.toggle("flag-resolved");
                title = changeStateButton.firstElementChild.classList.contains("flag-resolved")
                    ? 'Flag resolved'
                    : 'Resolve the flag';
                let rejectBtn = changeStateButton.parentElement.querySelector('.js-flag-reject');
                if (data.state === 4) {
                    if (rejectBtn) {
                        rejectBtn.firstElementChild.classList.remove("flag-rejected");
                        rejectBtn.setAttribute('title', 'Reject the flag');
                    }
                    commentBodyElement.classList.remove('flagged-comment');
                }
            }
            changeStateButton.setAttribute('title', title);
        });
    };

    document.addEventListener('click', (event) => {
        removeTargetElement(event);
        if (event.target && event.target !== event.currentTarget) {
            let modal = document.getElementById("Modal");
            let flagModal = document.getElementById('flagModal');
           if (event.target === modal || event.target === flagModal ||
               event.target.closest('.modal-close-btn') || event.target.closest('.modal-cancel-btn')) {
               hideModal(modal);
               hideModal(flagModal)
           }
           else if(event.target.closest('.js-reply-link')) {
               event.preventDefault();
               replyLink(event.target);
           }
           else if (event.target.closest('.js-comment-edit')) {
               event.preventDefault();
               setCommentForEditMode(event.target.closest('.js-comment-edit'));
           }
           else if (event.target.closest('.js-comment-cancel')) {
               event.preventDefault();
               cancelEdit(event.target.closest('.js-comment-cancel'));
           }
           else if (event.target.closest('.js-comment-delete')) {
               event.preventDefault();
               loadForm(event.target.closest('.js-comment-delete'));
           }
           else if (event.target.closest('.js-comment-reaction')) {
               event.preventDefault();
               submitReaction(event.target.closest('.js-comment-reaction'));
           }
           else if (event.target.closest('.js-comment-flag')) {
               event.preventDefault();
               setFlag(event.target.closest('.js-comment-flag'));
           }
           else if (event.target.closest('.js-read-more-btn')) {
               event.preventDefault();
               toggleText(event.target);
           }
           else if (event.target.closest('.js-flag-reject') || event.target.closest('.js-flag-resolve')) {
               event.preventDefault();
               toggleFlagState(event.target.closest('.js-flag-reject') || event.target.closest('.js-flag-resolve'));
           }
        }
    }, false);

    document.addEventListener('submit', event => {
        if (event.target && event.target !== event.currentTarget) {
            if (event.target.classList.contains('js-comment-form')) {
                event.preventDefault();
                if (event.target.querySelector('.js-comment-input').value.replace(/^\s+|\s+$/g, "").length !== 0) {
                    submitCommentCreateForm(event.target);
                }
            }
            else if (event.target.classList.contains('js-comment-edit-form')) {
                event.preventDefault();
                submitEditCommentForm(event.target);
            }
            else if (event.target.classList.contains('js-comment-delete-form')) {
                event.preventDefault();
                submitDeleteCommentForm(event.target);
            }
        }
    }, false);

    document.addEventListener('keyup', event => {
        if (event.target && event.target !== event.currentTarget && event.key === 'Enter' && event.ctrlKey) {
            event.preventDefault();
            let createForm = event.target.closest('.js-comment-form');
            let editForm = event.target.closest('.js-comment-edit-form');
            if (createForm && createForm.querySelector('.js-comment-input').value.replace(/^\s+|\s+$/g, "").length !== 0) {
                submitCommentCreateForm(createForm);
            }
            else if (editForm && editForm.querySelector('.js-comment-input').value.replace(/^\s+|\s+$/g, "").length !== 0) {
                submitEditCommentForm(editForm);
            }
        }
    }, false);

    ['input', 'keyup', 'focus'].forEach(item => {
        document.addEventListener(item, event => {
            if (event.target && event.target !== event.currentTarget) {
                if (event.target.classList.contains('js-comment-input')) {
                    event.preventDefault();
                    commentInput(event.target);
                }
            }
        }, false);
    });
});
