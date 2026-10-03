// Register the service worker so the app can be installed and read offline.
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => {});
  });
}

// Kitchen mode: bigger text and keep the screen awake while cooking.
document.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-kitchen-toggle]");
  if (!button) return;

  const on = document.body.classList.toggle("kitchen");
  button.setAttribute("aria-pressed", String(on));

  if (on && "wakeLock" in navigator) {
    try {
      window.kitchenWakeLock = await navigator.wakeLock.request("screen");
    } catch (error) {
      // Not allowed (e.g. low battery); kitchen mode still enlarges the text.
    }
  } else if (window.kitchenWakeLock) {
    window.kitchenWakeLock.release();
    window.kitchenWakeLock = null;
  }
});

// The wake lock is dropped when the app is hidden; take it again on return.
document.addEventListener("visibilitychange", async () => {
  if (document.visibilityState === "visible" && document.body.classList.contains("kitchen") && "wakeLock" in navigator) {
    try {
      window.kitchenWakeLock = await navigator.wakeLock.request("screen");
    } catch (error) {}
  }
});
