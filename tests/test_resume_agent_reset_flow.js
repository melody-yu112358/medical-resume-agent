const assert = require("node:assert/strict");
const test = require("node:test");

const { resetResumeConversation } = require("../demo/resume-agent/reset-flow.js");

test("delete failure preserves local state and does not create a new conversation", async () => {
  const calls = [];
  const completed = await resetResumeConversation({
    sessionId: "session-with-private-material",
    deleteSession: async (sessionId) => {
      calls.push(`delete:${sessionId}`);
      throw new Error("local service unavailable");
    },
    clearLocalState: () => calls.push("clear"),
    createConversation: async () => calls.push("create"),
    onDeleteError: (error) => calls.push(`error:${error.message}`),
  });

  assert.equal(completed, false);
  assert.deepEqual(calls, [
    "delete:session-with-private-material",
    "error:local service unavailable",
  ]);
});

test("successful delete clears local state before creating the replacement", async () => {
  const calls = [];
  const completed = await resetResumeConversation({
    sessionId: "existing-session",
    deleteSession: async () => calls.push("delete"),
    clearLocalState: () => calls.push("clear"),
    createConversation: async () => calls.push("create"),
    onDeleteError: () => calls.push("error"),
  });

  assert.equal(completed, true);
  assert.deepEqual(calls, ["delete", "clear", "create"]);
});
