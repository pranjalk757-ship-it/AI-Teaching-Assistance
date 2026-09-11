import { useEffect, useRef, useState } from "react";
import "./App.css";
import ReactMarkdown from "react-markdown";

function App() {
  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const textareaRef = useRef(null);
  const messagesEndRef = useRef(null);

  // =========================
  // LOAD CHAT HISTORY
  // =========================
  useEffect(() => {
    const savedChats = localStorage.getItem("cn-ai-chats");

    if (savedChats) {
      const parsedChats = JSON.parse(savedChats);
      setChats(parsedChats);

      if (parsedChats.length > 0) {
        setActiveChatId(parsedChats[0].id);
      }
    }
  }, []);

  // =========================
  // SAVE CHAT HISTORY
  // =========================

  useEffect(() => {
    localStorage.setItem("cn-ai-chats", JSON.stringify(chats));
  }, [chats]);

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
    if (!question.trim() || loading) return;

    let chatId = activeChatId;

    // Create chat automatically if none exists
    if (!chatId) {
      const newChat = {
        id: Date.now(),
        title: question.slice(0, 35),
        messages: [],
        createdAt: new Date().toISOString(),
      };

      chatId = newChat.id;

      setChats((prev) => [newChat, ...prev]);
      setActiveChatId(chatId);
    }

    const userQuestion = question.trim();

    // Add user message
    const userMessage = {
      id: Date.now(),
      role: "user",
      text: userQuestion,
    };

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

    setQuestion("");
    setLoading(true);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/chat",
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
        throw new Error("Backend error");
      }

      const data = await response.json();

      const assistantMessage = {
        id: Date.now() + 1,
        role: "assistant",
        text: data.answer,
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
      const errorMessage = {
        id: Date.now() + 1,
        role: "assistant",
        text: "Unable to connect to the AI server. Please make sure FastAPI is running.",
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

    setChats((prev) =>
      prev.filter((chat) => chat.id !== id)
    );

    if (activeChatId === id) {
      const remaining = chats.filter(
        (chat) => chat.id !== id
      );

      setActiveChatId(
        remaining.length > 0
          ? remaining[0].id
          : null
      );
    }
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
                <span>Computer Networks</span>
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
          <span className="plus">+</span>

          {sidebarOpen && (
            <span>New chat</span>
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
                <strong>Course grounded</strong>
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

            /* =========================
               WELCOME SCREEN
            ========================= */

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

                      <span>→</span>
                    </button>
                  )
                )}

              </div>

            </div>

          ) : (

            /* =========================
               MESSAGES
            ========================= */

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

                  <div className={`message ${message.role}`}>
                      {message.role === "assistant" ? (
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