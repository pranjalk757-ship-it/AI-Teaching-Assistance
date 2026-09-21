import { useEffect, useRef, useState } from "react";
import "./App.css";
import ReactMarkdown from "react-markdown";

function App() {
  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [loaded, setLoaded] = useState(false);

  const textareaRef = useRef(null);
  const messagesEndRef = useRef(null);

  // =========================
  // LOAD CHAT HISTORY
  // =========================

  useEffect(() => {
    try {
      const savedChats = localStorage.getItem("cn-ai-chats");

      if (savedChats) {
        const parsedChats = JSON.parse(savedChats);

        if (Array.isArray(parsedChats)) {
          setChats(parsedChats);

          if (parsedChats.length > 0) {
            setActiveChatId(parsedChats[0].id);
          }
        }
      }
    } catch (error) {
      console.error("Failed to load chat history:", error);
      localStorage.removeItem("cn-ai-chats");
    } finally {
      setLoaded(true);
    }
  }, []);

  // =========================
  // SAVE CHAT HISTORY
  // =========================

  useEffect(() => {
    if (!loaded) return;

    localStorage.setItem(
      "cn-ai-chats",
      JSON.stringify(chats)
    );
  }, [chats, loaded]);

  // =========================
  // SCROLL TO BOTTOM
  // =========================

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [chats, loading]);

  // =========================
  // CURRENT CHAT
  // =========================

  const activeChat = chats.find(
    (chat) => chat.id === activeChatId
  );

  const messages = activeChat?.messages || [];

  // =========================
  // NEW CHAT
  // =========================

  const createNewChat = () => {
    const newChat = {
      id: Date.now(),
      title: "New Chat",
      messages: [],
      createdAt: new Date().toISOString(),
    };

    setChats((prev) => [newChat, ...prev]);
    setActiveChatId(newChat.id);
    setQuestion("");

    setTimeout(() => {
      textareaRef.current?.focus();
    }, 100);
  };

  // =========================
  // SEND MESSAGE
  // =========================

  const sendMessage = async () => {
    const userQuestion = question.trim();

    if (!userQuestion || loading) return;

    const userMessage = {
      id: Date.now(),
      role: "user",
      text: userQuestion,
    };

    let chatId = activeChatId;

    // =========================
    // CREATE CHAT IF NEEDED
    // =========================

    if (!chatId) {
      chatId = Date.now();

      const newChat = {
        id: chatId,
        title: userQuestion.slice(0, 35),
        messages: [userMessage],
        createdAt: new Date().toISOString(),
      };

      setChats((prev) => [newChat, ...prev]);
      setActiveChatId(chatId);
    } else {
      setChats((prev) =>
        prev.map((chat) => {
          if (chat.id !== chatId) return chat;

          return {
            ...chat,
            title:
              chat.messages.length === 0
                ? userQuestion.slice(0, 35)
                : chat.title,
            messages: [...chat.messages, userMessage],
          };
        })
      );
    }

    setQuestion("");
    setLoading(true);

    try {
      const response = await fetch(
        "https://ai-teaching-assistant-xfut.onrender.com/chat",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            question: userQuestion,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(
          `Backend error: ${response.status}`
        );
      }

      const data = await response.json();

      const assistantMessage = {
        id: Date.now(),
        role: "assistant",
        text:
          data.answer ||
          "I could not generate an answer.",
      };

      setChats((prev) =>
        prev.map((chat) => {
          if (chat.id !== chatId) return chat;

          return {
            ...chat,
            messages: [
              ...chat.messages,
              assistantMessage,
            ],
          };
        })
      );
    } catch (error) {
      console.error("Chat error:", error);

      const errorMessage = {
        id: Date.now(),
        role: "assistant",
        text:
          "Unable to connect to the AI server. Please try again.",
      };

      setChats((prev) =>
        prev.map((chat) => {
          if (chat.id !== chatId) return chat;

          return {
            ...chat,
            messages: [
              ...chat.messages,
              errorMessage,
            ],
          };
        })
      );
    } finally {
      setLoading(false);

      setTimeout(() => {
        textareaRef.current?.focus();
      }, 100);
    }
  };

  // =========================
  // ENTER KEY
  // =========================

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // =========================
  // DELETE CHAT
  // =========================

  const deleteChat = (id, e) => {
    e.stopPropagation();

    setChats((prev) => {
      const remaining = prev.filter(
        (chat) => chat.id !== id
      );

      if (activeChatId === id) {
        setActiveChatId(
          remaining.length > 0
            ? remaining[0].id
            : null
        );
      }

      return remaining;
    });
  };

  // =========================
  // FORMAT HISTORY
  // =========================

  const todayChats = chats.filter((chat) => {
    const date = new Date(chat.createdAt);
    const today = new Date();

    return (
      date.toDateString() ===
      today.toDateString()
    );
  });

  const olderChats = chats.filter((chat) => {
    const date = new Date(chat.createdAt);
    const today = new Date();

    return (
      date.toDateString() !==
      today.toDateString()
    );
  });

  // =========================
  // SUGGESTIONS
  // =========================

  const suggestions = [
    "Explain the OSI model",
    "What is TCP?",
    "Explain IP addressing",
    "What is network topology?",
  ];

  const useSuggestion = (text) => {
    setQuestion(text);

    setTimeout(() => {
      textareaRef.current?.focus();
    }, 100);
  };

  return (
    <div className="app">

      {/* =========================
          SIDEBAR
      ========================= */}

      <aside
        className={`sidebar ${
          sidebarOpen ? "open" : "closed"
        }`}
      >

        <div className="sidebar-top">

          <div className="brand">

            <div className="brand-logo">
              AI
            </div>

            {sidebarOpen && (
              <div className="brand-text">
                <h2>AI Teaching</h2>
                <span>
                  Computer Networks
                </span>
              </div>
            )}

          </div>

          <button
            className="close-sidebar"
            onClick={() =>
              setSidebarOpen(false)
            }
          >
            ‹
          </button>

        </div>

        {/* NEW CHAT */}

        <button
          className="new-chat"
          onClick={createNewChat}
        >
          <span className="plus">
            +
          </span>

          {sidebarOpen && (
            <span>
              New chat
            </span>
          )}
        </button>

        {sidebarOpen && (
          <div className="history">

            {/* TODAY */}

            {todayChats.length > 0 && (
              <>
                <div className="history-title">
                  Today
                </div>

                {todayChats.map((chat) => (
                  <ChatHistoryItem
                    key={chat.id}
                    chat={chat}
                    active={
                      chat.id === activeChatId
                    }
                    onClick={() =>
                      setActiveChatId(chat.id)
                    }
                    onDelete={deleteChat}
                  />
                ))}
              </>
            )}

            {/* OLDER */}

            {olderChats.length > 0 && (
              <>
                <div className="history-title older">
                  Previous
                </div>

                {olderChats.map((chat) => (
                  <ChatHistoryItem
                    key={chat.id}
                    chat={chat}
                    active={
                      chat.id === activeChatId
                    }
                    onClick={() =>
                      setActiveChatId(chat.id)
                    }
                    onDelete={deleteChat}
                  />
                ))}
              </>
            )}

          </div>
        )}

        {/* SIDEBAR FOOTER */}

        {sidebarOpen && (
          <div className="sidebar-footer">

            <div className="course-status">

              <div className="status-dot"></div>

              <div>
                <strong>
                  Course grounded
                </strong>

                <span>
                  Answers from course material
                </span>
              </div>

            </div>

          </div>
        )}

      </aside>

      {/* =========================
          MAIN AREA
      ========================= */}

      <main className="main">

        {/* HEADER */}

        <header className="header">

          {!sidebarOpen && (
            <button
              className="open-sidebar"
              onClick={() =>
                setSidebarOpen(true)
              }
            >
              ☰
            </button>
          )}

          <div className="header-course">

            <div className="course-icon">
              CN
            </div>

            <div>
              <h3>
                Computer Networks
              </h3>

              <span>
                AI Teaching Assistant
              </span>
            </div>

          </div>

          <div className="header-right">
            <span className="online-dot"></span>
            Course only
          </div>

        </header>

        {/* =========================
            CHAT AREA
        ========================= */}

        <div className="chat-container">

          {messages.length === 0 ? (

            <div className="welcome">

              <div className="welcome-logo">
                <span>AI</span>
              </div>

              <h1>
                How can I help you?
              </h1>

              <p>
                Ask questions about your
                Computer Networks course.
              </p>

              <div className="grounded-message">

                <span className="check">
                  ✓
                </span>

                Answers are grounded in
                your course material

              </div>

              <div className="suggestions">

                {suggestions.map(
                  (suggestion) => (
                    <button
                      key={suggestion}
                      onClick={() =>
                        useSuggestion(
                          suggestion
                        )
                      }
                    >
                      {suggestion}

                      <span>
                        →
                      </span>
                    </button>
                  )
                )}

              </div>

            </div>

          ) : (

            <div className="messages">

              {messages.map((message) => (

                <div
                  key={message.id}
                  className={`message-row ${
                    message.role
                  }`}
                >

                  {message.role ===
                    "assistant" && (
                    <div className="avatar ai-avatar">
                      AI
                    </div>
                  )}

                  <div
                    className={`message ${
                      message.role
                    }`}
                  >
                    {message.role ===
                    "assistant" ? (
                      <ReactMarkdown>
                        {message.text}
                      </ReactMarkdown>
                    ) : (
                      message.text
                    )}
                  </div>

                  {message.role ===
                    "user" && (
                    <div className="avatar user-avatar">
                      U
                    </div>
                  )}

                </div>

              ))}

              {/* LOADING */}

              {loading && (
                <div className="message-row assistant">

                  <div className="avatar ai-avatar">
                    AI
                  </div>

                  <div className="message assistant loading-message">

                    <span></span>
                    <span></span>
                    <span></span>

                  </div>

                </div>
              )}

              <div ref={messagesEndRef}></div>

            </div>

          )}

        </div>

        {/* =========================
            INPUT
        ========================= */}

        <div className="input-area">

          <div className="input-box">

            <textarea
              ref={textareaRef}
              value={question}
              onChange={(e) =>
                setQuestion(e.target.value)
              }
              onKeyDown={handleKeyDown}
              placeholder="Ask about Computer Networks..."
              rows="1"
              disabled={loading}
            />

            <button
              className={`send-button ${
                question.trim()
                  ? "active"
                  : ""
              }`}
              onClick={sendMessage}
              disabled={
                !question.trim() ||
                loading
              }
            >
              ↑
            </button>

          </div>

          <div className="input-disclaimer">
            AI Teaching Assistant can make
            mistakes. Answers are based only
            on the provided course material.
          </div>

        </div>

      </main>

    </div>
  );
}


// =================================
// CHAT HISTORY ITEM
// =================================

function ChatHistoryItem({
  chat,
  active,
  onClick,
  onDelete,
}) {
  return (
    <div
      className={`history-item ${
        active ? "active" : ""
      }`}
      onClick={onClick}
    >

      <span className="history-icon">
        ◇
      </span>

      <span className="history-name">
        {chat.title}
      </span>

      <button
        className="delete-chat"
        onClick={(e) =>
          onDelete(chat.id, e)
        }
      >
        ×
      </button>

    </div>
  );
}

export default App;