(function exposeResetFlow(root, factory) {
  const resetFlow = factory();
  if (typeof module !== "undefined" && module.exports) module.exports = resetFlow;
  if (root) root.ResumeResetFlow = resetFlow;
}(typeof globalThis !== "undefined" ? globalThis : this, () => {
  async function resetResumeConversation({
    sessionId,
    deleteSession,
    clearLocalState,
    createConversation,
    onDeleteError,
  }) {
    if (sessionId) {
      try {
        await deleteSession(sessionId);
      } catch (error) {
        onDeleteError(error);
        return false;
      }
    }

    clearLocalState();
    await createConversation();
    return true;
  }

  return { resetResumeConversation };
}));
