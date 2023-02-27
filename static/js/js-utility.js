

const getCookie = (name) => {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


const removeAllChildNodes = (parent) => {
    while (parent.firstChild) {
        parent.removeChild(parent.firstChild);
    }
 }

/**
 * Safari does not allow for copy to clipboard in async functions
 * This is a workaround
 * See: https://developer.apple.com/forums/thread/691873, https://wolfgangrittner.dev/how-to-use-clipboard-api-in-firefox/
 * @param {function} call --expects function returning a fetch call that accepts application/text
 * @param {function} callback --if provided callback will run after text has been resolved
 */
const copyToClipboardAsync = (call, callback) => {

    const reponseToText = (response) => {
        const text = response.text()

        if (callback) {

            callback(text)
        }

        return text
    }

    if (typeof ClipboardItem && navigator.clipboard.write) {
        const text = new ClipboardItem({
            "text/plain": call()
                .then(reponseToText)
                .then(text => new Blob([text], { type: "text/plain" }))
        })
        navigator.clipboard.write([text])
    }
    else {
        call()
            .then(reponseToText)
            .then(text => navigator.clipboard.writeText(text))
    }
}