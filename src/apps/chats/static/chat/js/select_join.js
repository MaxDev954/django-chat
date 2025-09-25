const chatSelect = document.getElementById("chat-select");
const joinButton = document.getElementById("join");


chatSelect.addEventListener("change", function() {
    const selectedValue = chatSelect.value;

    if (selectedValue) {
        joinButton.href = `/chat/room/${selectedValue}/`;
    } else {
        joinButton.href = "#";
    }
});
