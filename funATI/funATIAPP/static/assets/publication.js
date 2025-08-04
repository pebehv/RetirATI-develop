function getCSRFToken() {
    var cookies = document.cookie.split(';');
    for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i].trim();
        if (cookie.startsWith('csrftoken=')) {
            return cookie.substring('csrftoken='.length, cookie.length);
        }
    }
    return '';
}
function showReplyForm(commentId) {
    document.querySelectorAll('.reply-form-container').forEach(function(el) {
        el.style.display = 'none';
    });
    var form = document.getElementById('reply-form-' + commentId);
    if (form) {
        form.style.display = 'block';
        var editable = form.querySelector('.reply-contenteditable');
        if (editable) editable.focus();
    }
}
// Placeholder y envío para el input de comentario principal
const COMMENT_PLACEHOLDER = 'Escribe un comentario...';
var commentSpan = document.getElementById('comment-content');
if (commentSpan) {
    if (!commentSpan.innerText.trim()) {
        commentSpan.innerText = COMMENT_PLACEHOLDER;
        commentSpan.classList.add('placeholder');
    }
    commentSpan.addEventListener('focus', function() {
        if (commentSpan.innerText.trim() === COMMENT_PLACEHOLDER) {
            commentSpan.innerText = '';
            commentSpan.classList.remove('placeholder');
        }
    });
    commentSpan.addEventListener('blur', function() {
        if (!commentSpan.innerText.trim()) {
            commentSpan.innerText = COMMENT_PLACEHOLDER;
            commentSpan.classList.add('placeholder');
        }
    });
    document.querySelector('.comment-form').addEventListener('submit', function(e) {
        e.preventDefault();
        var content = commentSpan.innerText.trim() === COMMENT_PLACEHOLDER ? '' : commentSpan.innerText.trim();
        var parent = document.getElementById('comment-parent-id').value;
        var csrf = getCSRFToken();
        var formData = new FormData();
        formData.append('content', content);
        formData.append('parent', parent);
        formData.append('csrfmiddlewaretoken', csrf);
        fetch(window.location.pathname, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        }).then(function(response) {
            if (response.ok) {
                window.location.reload();
            } else {
                alert('Error al enviar el comentario.');
            }
        });
    });
}
// Placeholder y envío para los formularios de respuesta
const REPLY_PLACEHOLDER = 'Escribe una respuesta...';
document.querySelectorAll('.reply-form').forEach(function(form) {
    var replySpan = form.querySelector('.reply-contenteditable');
    var hiddenInput = form.querySelector('.hidden-reply-content');
    if (replySpan) {
        if (!replySpan.innerText.trim()) {
            replySpan.innerText = REPLY_PLACEHOLDER;
            replySpan.classList.add('placeholder');
        }
        replySpan.addEventListener('focus', function() {
            if (replySpan.innerText.trim() === REPLY_PLACEHOLDER) {
                replySpan.innerText = '';
                replySpan.classList.remove('placeholder');
            }
        });
        replySpan.addEventListener('blur', function() {
            if (!replySpan.innerText.trim()) {
                replySpan.innerText = REPLY_PLACEHOLDER;
                replySpan.classList.add('placeholder');
            }
        });
    }
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        var content = replySpan.innerText.trim() === REPLY_PLACEHOLDER ? '' : replySpan.innerText.trim();
        var parent = form.querySelector('input[name="parent"]').value;
        var csrf = getCSRFToken();
        var formData = new FormData();
        formData.append('content', content);
        formData.append('parent', parent);
        formData.append('csrfmiddlewaretoken', csrf);
        fetch(window.location.pathname, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        }).then(function(response) {
            if (response.ok) {
                window.location.reload();
            } else {
                alert('Error al enviar la respuesta.');
            }
        });
    });
});
