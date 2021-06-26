var tx = document.getElementById("chat-box");

tx.height = tx.scrollHeight + "px";
tx.addEventListener("input", OnInput, false);

function OnInput() {
   if (tx.scrollHeight < document.getElementById("chat-content").clientHeight*(0.75)){
      this.style.height = (this.scrollHeight) + "px";
   }

   this.scrollTop = this.scrollHeight;
}

document.querySelector(".btn-expand").addEventListener("click", function() {
   document.getElementById("chat-log").classList.add("d-none");
   document.querySelector(".btn-expand").classList.add("d-none");
   document.querySelector(".btn-contract").classList.remove("d-none");
   tx.style.height = document.getElementById("chat-content").clientHeight + "px";

   tx.focus();

   tx.classList.add("is-expanded");
});

document.querySelector(".btn-contract").addEventListener("click", function() {
   if (document.body.clientWidth > 576) {
      tx.style.height = "175px";
   }
   else {
      tx.style.height = "125px";
   }
   document.getElementById("chat-log").classList.remove("d-none");
   document.querySelector(".btn-expand").classList.remove("d-none");
   document.querySelector(".btn-contract").classList.add("d-none");

   tx.classList.remove("is-expanded");
});

document.getElementById("chat-log").scrollTop = document.getElementById("chat-log").scrollHeight;
