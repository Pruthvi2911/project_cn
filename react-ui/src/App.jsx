import React, { useEffect, useState, useRef } from "react";
import {
  Box,
  Button,
  Container,
  TextField,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Avatar,
  Divider,
  Stack,
  Snackbar,
  Alert
} from "@mui/material";
import SendIcon from '@mui/icons-material/Send';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import axios from "axios";

const API_BASE = "http://127.0.0.1:8000";

export default function App() {
  const [messages, setMessages] = useState([]);
  const [user, setUser] = useState(() => localStorage.getItem("chat_user") || "webuser");
  const [text, setText] = useState("");
  const [file, setFile] = useState(null);
  const [uploads, setUploads] = useState([]);
  const [snack, setSnack] = useState(null);
  const listRef = useRef(null);

  useEffect(() => {
    localStorage.setItem("chat_user", user);
  }, [user]);

  const fetchMessages = async () => {
    try {
      const res = await axios.get(`${API_BASE}/messages`);
      setMessages(res.data || []);
    } catch (e) {
      // ignore
    }
  };

  useEffect(() => {
    fetchMessages();
    const t = setInterval(fetchMessages, 1000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    // auto-scroll
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages]);

  const sendChat = async () => {
    if (!text.trim()) return;
    try {
      await axios.post(`${API_BASE}/send_chat`, new URLSearchParams({ user, text }));
      setText("");
      fetchMessages();
    } catch (e) {
      setSnack({ severity: "error", message: "Failed to send" });
    }
  };

  const doUpload = async () => {
    if (!file) return setSnack({ severity: "warning", message: "Choose a file first" });
    const form = new FormData();
    form.append("user", user);
    form.append("file", file);
    try {
      const res = await axios.post(`${API_BASE}/upload`, form, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 30000
      });
      if (res.data?.status === "ok") {
        setSnack({ severity: "success", message: "Upload OK" });
        setUploads(u => [file.name, ...u]);
        setFile(null);
      } else {
        setSnack({ severity: "error", message: res.data?.msg || "Upload failed" });
      }
    } catch (e) {
      setSnack({ severity: "error", message: "Upload error" });
    }
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper sx={{ p: 2, display: "flex", alignItems: "center", mb: 2 }}>
        <Avatar sx={{ mr: 2 }}>💬</Avatar>
        <Box sx={{ flex: 1 }}>
          <Typography variant="h5">Realtime Chat + Upload</Typography>
          <Typography variant="caption" color="text.secondary">
            Backend: Flask + socket server · Frontend: React + MUI
          </Typography>
        </Box>
        <TextField
          value={user}
          size="small"
          onChange={(e) => setUser(e.target.value)}
          sx={{ width: 160 }}
        />
      </Paper>

      <Paper sx={{ display: "flex", height: 420 }}>
        <Box sx={{ width: "70%", borderRight: 1, borderColor: "divider", display: "flex", flexDirection: "column" }}>
          <Box ref={listRef} sx={{ flex: 1, overflowY: "auto", p: 2 }}>
            <List>
              {messages.map((m, i) => (
                <ListItem key={i} sx={{ alignItems: "flex-start" }}>
                  <ListItemText
                    primary={<strong>{m.user}</strong>}
                    secondary={
                      <>
                        <Typography component="span" variant="body2" color="text.primary">{m.text}</Typography>
                        <Typography component="div" sx={{ fontSize: 11, color: "text.secondary" }}>
                          {new Date(m.timestamp).toLocaleString()}
                        </Typography>
                      </>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Box>

          <Divider />

          <Box sx={{ display: "flex", gap: 1, p: 1 }}>
            <TextField
              fullWidth
              placeholder="Type a message..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") sendChat(); }}
              size="small"
            />
            <IconButton color="primary" onClick={sendChat}>
              <SendIcon />
            </IconButton>
          </Box>
        </Box>

        <Box sx={{ width: "30%", p: 2 }}>
          <Typography variant="h6">Uploads</Typography>
          <Stack spacing={1} sx={{ my: 1 }}>
            <input
              id="file"
              type="file"
              style={{ display: "block" }}
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
            <Button variant="contained" startIcon={<UploadFileIcon />} onClick={doUpload}>Upload</Button>
            <Typography variant="caption" color="text.secondary">Max file ~1 MB</Typography>
          </Stack>

          <Divider sx={{ my: 1 }} />

          <Typography variant="subtitle2">Recent uploads (session)</Typography>
          <List dense sx={{ maxHeight: 220, overflowY: "auto" }}>
            {uploads.length ? uploads.map((u, i) => (
              <ListItem key={i}><ListItemText primary={u} /></ListItem>
            )) : <ListItem><ListItemText secondary="No uploads yet" /></ListItem>}
          </List>
        </Box>
      </Paper>

      <Snackbar
        open={!!snack}
        autoHideDuration={3000}
        onClose={() => setSnack(null)}
      >
        {snack && <Alert severity={snack.severity} sx={{ width: "100%" }}>{snack.message}</Alert>}
      </Snackbar>
    </Container>
  );
}
