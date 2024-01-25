function addMessage(avatarUrl, username, message) {
  const text = message.replace(/\[red\](.*?)\[\/red\]/gi, '<span class="red">$1</span>')
                      .replace(/\[green\](.*?)\[\/green\]/gi, '<span class="green">$1</span>')
                      .replace(/\[yellow\](.*?)\[\/yellow\]/gi, '<span class="yellow">$1</span>')

  const container = document.getElementById("message-container");

  const messageElement = document.createElement("div");
  messageElement.classList.add("message");

  const avatarElement = document.createElement("img");
  avatarElement.src = avatarUrl;
  avatarElement.classList.add("avatar");
  messageElement.appendChild(avatarElement);

  const textElement = document.createElement("span");
  textElement.classList.add("text");
  textElement.innerHTML = '<span class="gray">' + username + '</span>' + text;
  messageElement.appendChild(textElement);

  container.insertBefore(messageElement, container.firstChild);
  messageElement.scrollIntoView();
}


const socket = io();
socket.on('connect', () => {
  console.log('Connected to the server');
});

socket.on('new_message', (data) => {
  addMessage(data.avatar_url, data.username, data.message);
});