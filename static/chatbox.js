const chatInput = document.querySelector(".messageinput textarea"); //gets the textInput field (textbox) from the base.html file and keeps a reference to that
const sendChatBtn = document.querySelector(".messageinput span"); //gets the span field (send button) from the base.html file and keeps a reference to that
const chatbox = document.querySelector(".chatbox"); //gets the chatbox from the base.html file and keeps a reference to that

let userMessage;

const createChatLi = (message, className) => {
    //creates a chat <li> element with the passed message and className
    const chatLi = document.createElement("li");
    chatLi.classList.add("chat", className);
    let chatContent = className === "outgoing" ? '<p>${message}</p>' : '<span class = "material-symbols-outlined">smart_toy</span><p>${message}</p>';
    chatLi.innerHTML = chatContent;
    return chatLi;
}

const handleChat = () => {
    userMessage = chatInput.value.trim(); //gets the text that the user has inputted within the chatInput field, and then trims extra whitespace
    if (!userMessage) return;

    //appends the message that the user typed to the chatbox
    chatbox.appendChild(createChatLi(userMessage, "outgoing"));
}

sendChatBtn.addEventListener("click", handleChat); //checks to see if the user has clicked on the span (send button), and runs the 'handleChat' const