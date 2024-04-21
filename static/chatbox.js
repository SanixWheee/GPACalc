const chatInput = document.querySelector(".messageinput textarea"); //gets the textInput field (textbox) from the base.html file and keeps a reference to that
const sendChatBtn = document.querySelector(".messageinput span"); //gets the span field (send button) from the base.html file and keeps a reference to that
const chatbox = document.querySelector(".chatbox"); //gets the chatbox from the base.html file and keeps a reference to that
const chatToggle = document.querySelector(".chatbutton"); //gets the button to open/close the chatbot from the base.html file and keeps a reference to that

let userMessage;

const url = "/api/assistant/create_message";
const inputHeight = chatInput.scrollHeight;

var fetchingResponse = false;

const createChatLi = (message, className) => {
    //creates a chat <li> element with the passed message and className
    const chatLi = document.createElement("li");
    chatLi.classList.add("chat", className);
    let chatContent = className === "outgoing" ? `<p>${message}</p>` : `<span class = "material-symbols-outlined">smart_toy</span><p>${message}</p>`;
    chatLi.innerHTML = chatContent;
    chatInput.value = '';
    return chatLi;
}

const generateResponse = (incomingMessage) => {
    fetchingResponse = true;

    const messageElement = incomingMessage.querySelector("p");
    const options = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            role: "user",
            content: userMessage,
            stream: true
        }),
    }
    fetch(url, options)
    .then(async (response) => {
        const reader = response.body.getReader()
        const decoder = new TextDecoder("utf-8");
        messageElement.textContent = "";

        while(true) {
            const word = await reader.read();
            const {done, value} = word;
            if (done) {
                fetchingResponse = false;
                break;
            }
            const decodedWord = decoder.decode(value);
            messageElement.textContent += decodedWord
        }
    })
    .catch((error) => {
        messageElement.textContent = "Oops! Something went wrong. Please try again!";
    })
}

const handleChat = () => {
    userMessage = chatInput.value.trim(); //gets the text that the user has inputted within the chatInput field, and then trims extra whitespace
    if (!userMessage) return;

    //appends the message that the user typed to the chatbox
    chatbox.appendChild(createChatLi(userMessage, "outgoing"));
    chatbox.scrollTo(0, chatbox.scrollHeight);

    const incomingMessage = createChatLi("Thinking...", "incoming");
    chatbox.appendChild(incomingMessage);
    generateResponse(incomingMessage);
    chatbox.scrollTo(0, chatbox.scrollHeight);
}



chatInput.addEventListener("keydown", (press) => {
    //Checks to see if the user presses the Enter key, while not pressing shift, and sends a message
    if (press.key === "Enter" && !press.shiftKey && !fetchingResponse) {
        press.preventDefault();
        handleChat();
    }
})

chatToggle.addEventListener("click", () => document.body.classList.toggle("showchatbot"));

sendChatBtn.addEventListener("click", handleChat); //checks to see if the user has clicked on the span (send button), and runs the 'handleChat' const