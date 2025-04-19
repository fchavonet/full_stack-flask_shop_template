/*****************************
* SCRIPT LOADED SUCCESSFULLY *
*****************************/

console.log("Flask Shop Template script loaded.");


/********************************
* BOOTSTRAP TOAST AUTO-LAUNCHER *
********************************/

const allToasts = [].slice.call(document.querySelectorAll(".toast"))
allToasts.map(function (toasts) {
  const toast = new bootstrap.Toast(toasts)
  toast.show()
})