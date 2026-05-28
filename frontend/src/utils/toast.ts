// Simple toast utility — replace with a proper lib (react-hot-toast) in sprint stories
const toast = {
  warn: (msg: string) => console.warn("[toast]", msg),
  error: (msg: string) => console.error("[toast]", msg),
  success: (msg: string) => console.log("[toast]", msg),
};
export default toast;
