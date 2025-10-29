import { useState, useEffect, useRef } from "react";
import "@/App.css";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2, Send, Database, ArrowRight } from "lucide-react";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [dataSummary, setDataSummary] = useState(null);
  const scrollRef = useRef(null);

  useEffect(() => {
    // Generate session ID
    setSessionId(`session_${Date.now()}`);
    
    // Fetch data summary
    fetchDataSummary();
  }, []);

  useEffect(() => {
    // Scroll to bottom when new messages arrive
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const fetchDataSummary = async () => {
    try {
      const response = await axios.get(`${API}/data/summary`);
      setDataSummary(response.data);
    } catch (error) {
      console.error("Error fetching data summary:", error);
      toast.error("Failed to load data summary");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim() || loading) return;

    const userQuestion = question;
    setQuestion("");
    
    // Add user message
    setMessages(prev => [...prev, { type: 'user', text: userQuestion }]);
    setLoading(true);

    try {
      const response = await axios.post(`${API}/qa/ask`, {
        question: userQuestion,
        session_id: sessionId
      });

      // Add AI response
      setMessages(prev => [...prev, {
        type: 'assistant',
        text: response.data.answer,
        sources: response.data.data_sources,
        data: response.data.data_used
      }]);

    } catch (error) {
      console.error("Error asking question:", error);
      toast.error("Failed to get answer. Please try again.");
      setMessages(prev => [...prev, {
        type: 'error',
        text: 'Sorry, I encountered an error processing your question. Please try again.'
      }]);
    } finally {
      setLoading(false);
    }
  };

  const sampleQuestions = [
    "Compare average annual rainfall in Maharashtra and Karnataka for the last 10 years",
    "What are the top 5 most produced crops in Punjab between 2010-2015?",
    "Analyze rice production trends in West Bengal from 2000 to 2015",
    "Which district in Uttar Pradesh had the highest wheat production in 2015?"
  ];

  return (
    <div className="App">
      <div className="main-container">
        {/* Header */}
        <header className="app-header">
          <div className="header-content">
            <div className="logo-section">
              <Database className="logo-icon" />
              <div>
                <h1 className="title">Project Samarth</h1>
                <p className="subtitle">Intelligent Q&A System for Agricultural & Climate Data</p>
              </div>
            </div>
            {dataSummary && (
              <div className="data-stats">
                <div className="stat-item">
                  <span className="stat-value">{dataSummary.crop_production?.states?.length || 0}</span>
                  <span className="stat-label">States</span>
                </div>
                <div className="stat-item">
                  <span className="stat-value">{dataSummary.crop_production?.crops?.length || 0}</span>
                  <span className="stat-label">Crops</span>
                </div>
                <div className="stat-item">
                  <span className="stat-value">
                    {dataSummary.crop_production?.year_range ? 
                      `${dataSummary.crop_production.year_range[0]}-${dataSummary.crop_production.year_range[1]}` : 
                      'N/A'}
                  </span>
                  <span className="stat-label">Years</span>
                </div>
              </div>
            )}
          </div>
        </header>

        {/* Main Content */}
        <div className="content-area">
          {messages.length === 0 ? (
            <div className="welcome-section">
              <div className="welcome-card">
                <h2 className="welcome-title">Ask me anything about Indian agriculture and climate</h2>
                <p className="welcome-text">
                  I can analyze data from Ministry of Agriculture and IMD to answer your questions about
                  crop production, rainfall patterns, and their correlations.
                </p>
                
                <div className="sample-questions">
                  <h3 className="sample-title">Sample Questions:</h3>
                  <div className="questions-grid">
                    {sampleQuestions.map((q, idx) => (
                      <button
                        key={idx}
                        data-testid={`sample-question-${idx}`}
                        className="sample-question-btn"
                        onClick={() => setQuestion(q)}
                      >
                        <ArrowRight className="question-icon" />
                        <span>{q}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <ScrollArea className="messages-area" ref={scrollRef}>
              <div className="messages-container">
                {messages.map((msg, idx) => (
                  <div key={idx} className={`message message-${msg.type}`} data-testid={`message-${msg.type}-${idx}`}>
                    {msg.type === 'user' ? (
                      <div className="message-content user-message">
                        <p>{msg.text}</p>
                      </div>
                    ) : (
                      <div className="message-content assistant-message">
                        <div className="answer-text">{msg.text}</div>
                        {msg.sources && msg.sources.length > 0 && (
                          <div className="sources-section">
                            <p className="sources-title">Data Sources:</p>
                            <ul className="sources-list">
                              {msg.sources.map((source, i) => (
                                <li key={i}>{source}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
                {loading && (
                  <div className="message message-assistant" data-testid="loading-indicator">
                    <div className="message-content assistant-message">
                      <Loader2 className="loader-icon" />
                      <span>Analyzing data and generating response...</span>
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>
          )}
        </div>

        {/* Input Area */}
        <div className="input-area">
          <form onSubmit={handleSubmit} className="input-form">
            <Input
              data-testid="question-input"
              type="text"
              placeholder="Ask a question about crop production, rainfall, or climate patterns..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              disabled={loading}
              className="question-input"
            />
            <Button 
              data-testid="submit-question-btn"
              type="submit" 
              disabled={loading || !question.trim()}
              className="submit-btn"
            >
              {loading ? <Loader2 className="btn-icon spinning" /> : <Send className="btn-icon" />}
              Ask
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default App;