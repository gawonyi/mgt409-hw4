// Lets any page open the chat with a question ready to send (used by "Ask about this item").
export const ASK_EVENT = "cc:ask-chat";

export function askInChat(text: string) {
  window.dispatchEvent(new CustomEvent<string>(ASK_EVENT, { detail: text }));
}
