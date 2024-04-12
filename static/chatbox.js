const chatInput = document.querySelector(".messageinput textarea"); //gets the textInput field (textbox) from the base.html file and keeps a reference to that
const sendChatBtn = document.querySelector(".messageinput span"); //gets the span field (send button) from the base.html file and keeps a reference to that
const chatbox = document.querySelector(".chatbox"); //gets the chatbox from the base.html file and keeps a reference to that
const chatToggle = document.querySelector(".chatbutton"); //gets the button to open/close the chatbot from the base.html file and keeps a reference to that

let userMessage;

const inputHeight = chatInput.scrollHeight;

const createChatLi = (message, className) => {
    //creates a chat <li> element with the passed message and className
    const chatLi = document.createElement("li");
    chatLi.classList.add("chat", className);
    let chatContent = className === "outgoing" ? `<p>${message}</p>` : `<span class = "material-symbols-outlined">smart_toy</span><p>${message}</p>`;
    chatLi.innerHTML = chatContent;
    chatInput.value = '';
    return chatLi;
}

const handleChat = () => {
    userMessage = chatInput.value.trim(); //gets the text that the user has inputted within the chatInput field, and then trims extra whitespace
    if (!userMessage) return;
    //send post request to /api/assistant/create_message here, content would be userMessage

    //appends the message that the user typed to the chatbox
    chatbox.appendChild(createChatLi(userMessage, "outgoing"));
    chatbox.scrollTo(0, chatbox.scrollHeight);

    setTimeout(() => {
        const incomingMessage = createChatLi("Thinking...", "incoming")
        chatbox.appendChild(incomingMessage);
        chatbox.scrollTo(0, chatbox.scrollHeight);
    }, 600);
}

// chatInput.addEventListener("input", () => {
//     //adjusts the height of the input box depending on how much the user types
//     chatInput.style.height = `${inputHeight}px`;
//     chatInput.style.height = `${chatInput.scrollHeight}px`;

// })

chatInput.addEventListener("keydown", (press) => {
    //Checks to see if the user presses the Enter key, while not pressing shift, and sends a message
    if (press.key === "Enter" && !press.shiftKey && window.innerWidth > 800) {
        press.preventDefault();
        handleChat();
    }

})

chatToggle.addEventListener("click", () => document.body.classList.toggle("showchatbot"));

sendChatBtn.addEventListener("click", handleChat); //checks to see if the user has clicked on the span (send button), and runs the 'handleChat' const