import { useEffect, useMemo, useState } from "react";
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Paper,
  Stack,
  Button,
  IconButton,
  TextField,
  Chip,
  Snackbar,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider,
  Box,
  Tooltip,
  useMediaQuery,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import RefreshIcon from "@mui/icons-material/Refresh";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import SyncIcon from "@mui/icons-material/Sync";
import { useTheme } from "@mui/material/styles";


import {
  type SubscriptionSource,
  type SubType,
  listSubs,
  addSub,
  updateSub,
  deleteSub,
  refreshSubCache,
} from "./api";

type Toast = { severity: "success" | "error" | "info"; msg: string } | null;

const SUB_TYPES: SubType[] = ["remote", "local"];

function SubTypeChip({ t }: { t: SubType }) {
  return (
    <Chip
      size="small"
      label={t}
      variant="outlined"
      sx={{ width: 80, textTransform: "uppercase" }}
    />
  );
}

function buildSubLink(id: number) {
  // 复制“绝对链接”，方便粘贴到 mihomo/clash/subconverter 任意地方
  return `${window.location.origin}/sub/${id}`;
}

async function copyText(text: string) {
  // clipboard 在 https/localhost 下可用；失败就 fallback
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    // fallback: 用隐藏 textarea
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    const ok = document.execCommand("copy");
    document.body.removeChild(ta);
    return ok;
  }
}

export default function App() {
  const [rows, setRows] = useState<SubscriptionSource[]>([]);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState<Toast>(null);

  const [query, setQuery] = useState("");

  // dialog
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<"add" | "edit">("add");
  const [editing, setEditing] = useState<SubscriptionSource | null>(null);

  // form
  const [name, setName] = useState("");
  const [type, setType] = useState<SubType>("remote");
  const [url, setUrl] = useState("");
  const [content, setContent] = useState("");

  // refreshing state
  const [refreshingId, setRefreshingId] = useState<number | null>(null);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return rows;
    return rows.filter((r) => {
      return (
        r.name.toLowerCase().includes(q) ||
        String(r.id).includes(q) ||
        (r.url ?? "").toLowerCase().includes(q) ||
        r.type.toLowerCase().includes(q)
      );
    });
  }, [rows, query]);

  async function refresh() {
    setLoading(true);
    try {
      const data = await listSubs();
      setRows(data);
    } catch (e: any) {
      setToast({ severity: "error", msg: e.message || String(e) });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  function openAdd() {
    setMode("add");
    setEditing(null);
    setName("");
    setType("remote");
    setUrl("");
    setContent("");
    setOpen(true);
  }

  function openEdit(r: SubscriptionSource) {
    setMode("edit");
    setEditing(r);
    setName(r.name);
    setType(r.type);
    setUrl(r.url ?? "");
    setContent("");
    setOpen(true);
  }

  async function handleCopyLink(id: number) {
    const link = buildSubLink(id);
    const ok = await copyText(link);
    setToast({
      severity: ok ? "success" : "error",
      msg: ok ? "Subscription link copied" : "Copy failed",
    });
  }

  async function handleSave() {
    try {
      if (mode === "add") {
        if (!name.trim()) throw new Error("Name is required");
        if (type === "remote" && !url.trim()) throw new Error("URL is required");
        if (type === "local" && !content.trim())
          throw new Error("Content is required");

        const payload: any = { name: name.trim(), type };
        if (type === "remote") payload.url = url.trim();
        else payload.content = content;

        const res = await addSub(payload);
        setToast({ severity: "success", msg: `Added (id=${res.id})` });
      } else {
        if (!editing) throw new Error("No editing item");
        if (type === "remote" && !url.trim()) throw new Error("URL is required");
        if (type === "local" && !content.trim())
          throw new Error("Content is required");

        const payload: any = { type };
        if (type === "remote") payload.url = url.trim();
        else payload.content = content;

        await updateSub(editing.id, payload);
        setToast({ severity: "success", msg: "Updated" });
      }

      setOpen(false);
      await refresh();
    } catch (e: any) {
      setToast({ severity: "error", msg: e.message || String(e) });
    }
  }

  async function handleDelete(r: SubscriptionSource) {
    const ok = confirm(`Delete subscription #${r.id} (${r.name}) ?`);
    if (!ok) return;

    try {
      await deleteSub(r.id);
      setToast({ severity: "success", msg: "Deleted" });
      await refresh();
    } catch (e: any) {
      setToast({ severity: "error", msg: e.message || String(e) });
    }
  }

  async function handleRefreshCache(r: SubscriptionSource) {
    if (r.type !== "remote") {
      setToast({ severity: "info", msg: "Only remote subscriptions can be refreshed" });
      return;
    }

    try {
      setRefreshingId(r.id);
      await refreshSubCache(r.id);
      setToast({ severity: "success", msg: "Cache refreshed" });
      await refresh();
    } catch (e: any) {
      setToast({ severity: "error", msg: e.message || String(e) });
    } finally {
      setRefreshingId(null);
    }
  }

  // For mobile devices
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));

  return (
    <>
      <AppBar position="sticky">
        <Toolbar>
          <Typography variant="h6" sx={{ flex: 1 }}>
            Sub Cache UI
          </Typography>
          <IconButton color="inherit" onClick={refresh} title="Refresh">
            <RefreshIcon />
          </IconButton>
          <Button color="inherit" startIcon={<AddIcon />} onClick={openAdd}>
            Add
          </Button>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ py: 3 }}>
        <Paper sx={{ p: 2 }}>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
            <TextField
              label="Search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              fullWidth
            />
          </Stack>

          <Divider sx={{ my: 2 }} />

          <Stack spacing={1}>
            {filtered.map((r) => (
              <Paper
                key={r.id}
                variant="outlined"
                sx={{
                  p: 1.5,
                  display: "flex",
                  gap: 1.5,
                  flexDirection: { xs: "column", sm: "row" },
                  alignItems: { xs: "stretch", sm: "center" },
                  overflow: "hidden",
                }}
              >
                <Typography sx={{ fontWeight: 600, width: { xs: "auto", sm: 70 } }}>
                  #{r.id}
                </Typography>

                <SubTypeChip t={r.type} />

                <Box sx={{ flex: 1, minWidth: 0}}>
                  <Typography sx={{ fontWeight: 600 }} noWrap={!isMobile}>
                    {r.name}
                  </Typography>

                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      gap: 1,
                      mt: 0.5,
                      flexWrap: { xs: "wrap", sm: "nowrap" },
                      minWidth: 0,
                    }}
                  >
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{ minWidth: 0, flex: 1 }}
                      noWrap={!isMobile}
                    >
                      {r.type === "remote" ? r.url : "(local content)"}
                    </Typography>

                    <Chip
                      size="small"
                      label={`/sub/${r.id}`}
                      variant="outlined"
                      sx={{ flexShrink: 0 }}
                    />
                  </Box>
                </Box>

                <Stack
                  direction="row"
                  spacing={isMobile ? 0.5 : 1}
                  sx={{
                    justifyContent: { xs: "flex-end", sm: "flex-start" },
                    flexWrap: { xs: "wrap", sm: "nowrap" },
                    whiteSpace: "nowrap",
                    flexShrink: 0,
                    alignItems: "center",
                  }}
                >
                  <Tooltip title="Copy subscription link">
                    <IconButton size={isMobile ? "small" : "medium"} onClick={() => handleCopyLink(r.id)}>
                      <ContentCopyIcon fontSize={isMobile ? "small" : "medium"} />
                    </IconButton>
                  </Tooltip>

                  <Tooltip title="Edit">
                    <IconButton size={isMobile ? "small" : "medium"} onClick={() => openEdit(r)}>
                      <EditIcon fontSize={isMobile ? "small" : "medium"} />
                    </IconButton>
                  </Tooltip>

                  <Tooltip title={r.type === "remote" ? "Refresh cache" : "Only remote can refresh"}>
                    <span>
                      <IconButton
                        size={isMobile ? "small" : "medium"}
                        onClick={() => handleRefreshCache(r)}
                        disabled={r.type !== "remote" || refreshingId === r.id}
                      >
                        {refreshingId === r.id ? (
                          <CircularProgress size={isMobile ? 16 : 20} />
                        ) : (
                          <SyncIcon fontSize={isMobile ? "small" : "medium"} />
                        )}
                      </IconButton>
                    </span>
                  </Tooltip>

                  <Tooltip title="Delete">
                    <IconButton
                      size={isMobile ? "small" : "medium"}
                      onClick={() => handleDelete(r)}
                      color="error"
                    >
                      <DeleteIcon fontSize={isMobile ? "small" : "medium"} />
                    </IconButton>
                  </Tooltip>
                </Stack>
              </Paper>
            ))}

            {!loading && filtered.length === 0 && (
              <Typography color="text.secondary">
                No subscriptions found.
              </Typography>
            )}
          </Stack>
        </Paper>
      </Container>

      <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>
          {mode === "add" ? "Add Subscription" : "Edit Subscription"}
        </DialogTitle>

        <DialogContent sx={{ pt: 2 }}>
          <Stack spacing={2} sx={{ mt: 1 }}>
            {mode === "add" ? (
              <TextField
                label="Name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                fullWidth
              />
            ) : (
              <TextField label="Name" value={name} fullWidth disabled />
            )}

            <FormControl fullWidth>
              <InputLabel>Type</InputLabel>
              <Select
                label="Type"
                value={type}
                onChange={(e) => setType(e.target.value as SubType)}
              >
                {SUB_TYPES.map((t) => (
                  <MenuItem key={t} value={t}>
                    {t}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {type === "remote" ? (
              <TextField
                label="Remote URL"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                fullWidth
              />
            ) : (
              <TextField
                label="Local YAML Content"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                fullWidth
                multiline
                minRows={8}
                placeholder="Paste your Mihomo YAML here"
              />
            )}
          </Stack>
        </DialogContent>

        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSave}>
            Save
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={!!toast}
        autoHideDuration={3500}
        onClose={() => setToast(null)}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        {toast ? (
          <Alert severity={toast.severity} onClose={() => setToast(null)}>
            {toast.msg}
          </Alert>
        ) : undefined}
      </Snackbar>
    </>
  );
}
