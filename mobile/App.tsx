import * as SecureStore from 'expo-secure-store';
import { StatusBar } from 'expo-status-bar';
import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

const API_URL_KEY = 'api-base-url';
const API_TOKEN_KEY = 'api-bearer-token';

type Screen = 'console' | 'connection';
type LinkState = 'unknown' | 'checking' | 'connected' | 'error';
type Simulation = {
  title: string;
  summary: string;
  traceLength: number;
};

function normalizeApiUrl(value: string): string {
  let parsed: URL;
  try {
    parsed = new URL(value.trim());
  } catch {
    throw new Error('Enter a valid HTTPS API address.');
  }

  if (parsed.protocol !== 'https:') {
    throw new Error('Use an HTTPS address to protect credentials and telemetry.');
  }

  return parsed.toString().replace(/\/$/, '');
}

function authorizationHeaders(token: string): HeadersInit {
  return token.trim() ? { Authorization: `Bearer ${token.trim()}` } : {};
}

export default function App() {
  const [screen, setScreen] = useState<Screen>('console');
  const [apiUrl, setApiUrl] = useState('');
  const [token, setToken] = useState('');
  const [linkState, setLinkState] = useState<LinkState>('unknown');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('Connect to your secured API to begin.');
  const [simulation, setSimulation] = useState<Simulation | null>(null);

  useEffect(() => {
    let mounted = true;
    void Promise.all([
      SecureStore.getItemAsync(API_URL_KEY),
      SecureStore.getItemAsync(API_TOKEN_KEY),
    ]).then(([savedUrl, savedToken]) => {
      if (!mounted) return;
      if (savedUrl) setApiUrl(savedUrl);
      if (savedToken) setToken(savedToken);
      if (savedUrl) setMessage('Saved connection loaded. Verify it before running.');
    });
    return () => {
      mounted = false;
    };
  }, []);

  async function checkConnection(urlValue: string, tokenValue: string) {
    const baseUrl = normalizeApiUrl(urlValue);
    const headers = authorizationHeaders(tokenValue);
    const healthResponse = await fetch(`${baseUrl}/health`);
    if (!healthResponse.ok) throw new Error(`Health check returned ${healthResponse.status}.`);

    const configResponse = await fetch(`${baseUrl}/config`, { headers });
    if (configResponse.status === 401) throw new Error('Authentication failed. Check the API token.');
    if (!configResponse.ok) throw new Error(`API check returned ${configResponse.status}.`);
    return baseUrl;
  }

  async function saveAndConnect() {
    setBusy(true);
    setLinkState('checking');
    setMessage('Checking HTTPS and API authentication...');
    try {
      const baseUrl = await checkConnection(apiUrl, token);
      await SecureStore.setItemAsync(API_URL_KEY, baseUrl);
      if (token.trim()) {
        await SecureStore.setItemAsync(API_TOKEN_KEY, token.trim());
      } else {
        await SecureStore.deleteItemAsync(API_TOKEN_KEY);
      }
      setApiUrl(baseUrl);
      setLinkState('connected');
      setMessage('API connected. Credentials are stored in device secure storage.');
      setScreen('console');
    } catch (error) {
      setLinkState('error');
      setMessage(error instanceof Error ? error.message : 'Could not connect to the API.');
    } finally {
      setBusy(false);
    }
  }

  async function runSimulation(kind: 'agent' | 'battery') {
    setBusy(true);
    setMessage(`Running ${kind} simulation...`);
    try {
      const baseUrl = normalizeApiUrl(apiUrl);
      const path = kind === 'agent'
        ? '/agent/simulate?steps=30&seed=42'
        : '/battery/simulate?steps=30&seed=42';
      const response = await fetch(`${baseUrl}${path}`, {
        method: 'POST',
        headers: authorizationHeaders(token),
      });
      const body = await response.json() as Record<string, unknown>;
      if (response.status === 401) throw new Error('Authentication failed. Reconnect with a valid API token.');
      if (!response.ok) {
        const detail = typeof body.detail === 'string' ? body.detail : `Request failed (${response.status}).`;
        throw new Error(detail);
      }
      const summary = body.summary && typeof body.summary === 'object'
        ? body.summary as Record<string, unknown>
        : {};
      const trace = Array.isArray(body.trace) ? body.trace : [];
      setSimulation({
        title: kind === 'agent' ? 'Agent simulation' : 'Battery simulation',
        summary: Object.entries(summary)
          .map(([key, value]) => `${key.replaceAll('_', ' ')}: ${String(value)}`)
          .join('\n'),
        traceLength: trace.length,
      });
      setLinkState('connected');
      setMessage('Simulation complete. No aircraft commands were sent.');
    } catch (error) {
      setLinkState('error');
      setMessage(error instanceof Error ? error.message : 'Simulation request failed.');
    } finally {
      setBusy(false);
    }
  }

  const stateColor = linkState === 'connected'
    ? styles.goodText
    : linkState === 'error'
      ? styles.errorText
      : styles.mutedText;

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <View style={styles.topline}>
          <View>
            <Text style={styles.kicker}>EMBODIED AGENCY</Text>
            <Text style={styles.title}>FIELD CONSOLE</Text>
          </View>
          <View style={styles.onlineMark}>
            <View style={[styles.dot, linkState === 'connected' && styles.dotOn]} />
            <Text style={styles.markText}>{linkState === 'connected' ? 'API LIVE' : 'API OFFLINE'}</Text>
          </View>
        </View>

        <View style={styles.notice}>
          <View style={styles.noticeHeader}>
            <Text style={styles.noticeLabel}>AIRCRAFT LINK</Text>
            <Text style={styles.noticeState}>NOT CONNECTED</Text>
          </View>
          <Text style={styles.noticeTitle}>DJI Mavic 4</Text>
          <Text style={styles.noticeCopy}>
            Simulator-only mode. No DJI SDK connection or flight commands are enabled.
          </Text>
        </View>

        <View style={styles.tabs}>
          <Pressable
            accessibilityRole="tab"
            accessibilityState={{ selected: screen === 'console' }}
            onPress={() => setScreen('console')}
            style={[styles.tab, screen === 'console' && styles.activeTab]}
          >
            <Text style={[styles.tabText, screen === 'console' && styles.activeTabText]}>Console</Text>
          </Pressable>
          <Pressable
            accessibilityRole="tab"
            accessibilityState={{ selected: screen === 'connection' }}
            onPress={() => setScreen('connection')}
            style={[styles.tab, screen === 'connection' && styles.activeTab]}
          >
            <Text style={[styles.tabText, screen === 'connection' && styles.activeTabText]}>Connection</Text>
          </Pressable>
        </View>

        {screen === 'console' ? (
          <View>
            <View style={styles.sectionHeading}>
              <Text style={styles.sectionIndex}>01 / SIMULATION</Text>
              <Text style={styles.sectionTitle}>Run a model</Text>
              <Text style={styles.sectionCopy}>Seeded runs use the existing backend models.</Text>
            </View>

            <View style={styles.actionRow}>
              <Pressable
                accessibilityRole="button"
                disabled={busy || !apiUrl}
                onPress={() => void runSimulation('agent')}
                style={[styles.actionButton, styles.agentButton, (busy || !apiUrl) && styles.disabledButton]}
              >
                <Text style={styles.actionIndex}>A / 30 STEPS</Text>
                <Text style={styles.actionTitle}>Run agent</Text>
                <Text style={styles.actionArrow}>START  {'>'}</Text>
              </Pressable>
              <Pressable
                accessibilityRole="button"
                disabled={busy || !apiUrl}
                onPress={() => void runSimulation('battery')}
                style={[styles.actionButton, styles.batteryButton, (busy || !apiUrl) && styles.disabledButton]}
              >
                <Text style={styles.actionIndex}>B / 30 STEPS</Text>
                <Text style={styles.actionTitle}>Run battery</Text>
                <Text style={styles.actionArrow}>START  {'>'}</Text>
              </Pressable>
            </View>

            <View style={styles.resultSection}>
              <View style={styles.resultHeading}>
                <Text style={styles.sectionIndex}>02 / LATEST RESULT</Text>
                {busy ? <ActivityIndicator color="#c3f36b" /> : null}
              </View>
              {simulation ? (
                <View>
                  <Text style={styles.resultTitle}>{simulation.title}</Text>
                  <Text style={styles.resultMeta}>{simulation.traceLength} trace samples</Text>
                  <Text selectable style={styles.resultBody}>{simulation.summary || 'No summary values returned.'}</Text>
                </View>
              ) : (
                <Text style={styles.emptyResult}>No simulation run in this session.</Text>
              )}
            </View>
          </View>
        ) : (
          <View style={styles.connectionSection}>
            <Text style={styles.sectionIndex}>03 / SECURE CONNECTION</Text>
            <Text style={styles.sectionTitle}>API endpoint</Text>
            <Text style={styles.sectionCopy}>Use a publicly reachable HTTPS address with a valid TLS certificate.</Text>

            <Text style={styles.inputLabel}>HTTPS BASE URL</Text>
            <TextInput
              accessibilityLabel="HTTPS API base URL"
              autoCapitalize="none"
              autoCorrect={false}
              keyboardType="url"
              onChangeText={setApiUrl}
              placeholder="https://api.example.com"
              placeholderTextColor="#73817d"
              style={styles.input}
              value={apiUrl}
            />

            <Text style={styles.inputLabel}>API BEARER TOKEN</Text>
            <TextInput
              accessibilityLabel="API bearer token"
              autoCapitalize="none"
              autoCorrect={false}
              onChangeText={setToken}
              placeholder="Paste deployment token"
              placeholderTextColor="#73817d"
              secureTextEntry
              style={styles.input}
              value={token}
            />

            <Pressable
              accessibilityRole="button"
              disabled={busy}
              onPress={() => void saveAndConnect()}
              style={[styles.connectButton, busy && styles.disabledButton]}
            >
              {busy ? <ActivityIndicator color="#111813" /> : <Text style={styles.connectButtonText}>SAVE AND VERIFY</Text>}
            </Pressable>
            <Text style={[styles.statusMessage, stateColor]}>{message}</Text>
            <Text style={styles.credentialNote}>The token is stored using iOS Keychain or Android Keystore.</Text>
          </View>
        )}

        <View style={styles.footer}>
          <Text style={styles.footerText}>MODEL ACCESS: SIMULATED</Text>
          <Text style={styles.footerText}>FLIGHT CONTROL: DISABLED</Text>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#111813' },
  content: { paddingHorizontal: 22, paddingTop: 62, paddingBottom: 36, maxWidth: 680, width: '100%', alignSelf: 'center' },
  topline: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 },
  kicker: { color: '#c3f36b', fontSize: 11, fontWeight: '700', letterSpacing: 1.2 },
  title: { color: '#f2f4eb', fontSize: 23, fontWeight: '800', marginTop: 5 },
  onlineMark: { flexDirection: 'row', alignItems: 'center', gap: 7 },
  dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: '#ee7658' },
  dotOn: { backgroundColor: '#c3f36b' },
  markText: { color: '#bbc5bb', fontSize: 10, fontWeight: '700' },
  notice: { backgroundColor: '#202b24', borderLeftWidth: 3, borderLeftColor: '#ee7658', padding: 16, marginBottom: 24 },
  noticeHeader: { flexDirection: 'row', justifyContent: 'space-between', gap: 10 },
  noticeLabel: { color: '#a4b3a5', fontSize: 10, fontWeight: '700' },
  noticeState: { color: '#ff9a7c', fontSize: 10, fontWeight: '800' },
  noticeTitle: { color: '#f2f4eb', fontSize: 19, fontWeight: '700', marginTop: 12 },
  noticeCopy: { color: '#b6c2b8', fontSize: 13, lineHeight: 19, marginTop: 5 },
  tabs: { flexDirection: 'row', borderBottomWidth: 1, borderColor: '#344238', marginBottom: 27 },
  tab: { paddingVertical: 12, paddingHorizontal: 16, borderBottomWidth: 2, borderBottomColor: 'transparent' },
  activeTab: { borderBottomColor: '#c3f36b' },
  tabText: { color: '#9ca99d', fontSize: 14, fontWeight: '600' },
  activeTabText: { color: '#f2f4eb' },
  sectionHeading: { marginBottom: 18 },
  sectionIndex: { color: '#c3f36b', fontSize: 10, fontWeight: '700', letterSpacing: 0.8 },
  sectionTitle: { color: '#f2f4eb', fontSize: 22, fontWeight: '700', marginTop: 8 },
  sectionCopy: { color: '#9eaaa0', fontSize: 13, lineHeight: 19, marginTop: 5 },
  actionRow: { flexDirection: 'row', gap: 12 },
  actionButton: { flex: 1, minHeight: 142, padding: 14, justifyContent: 'space-between' },
  agentButton: { backgroundColor: '#d6ebbc' },
  batteryButton: { backgroundColor: '#9ed9cf' },
  actionIndex: { color: '#465545', fontSize: 10, fontWeight: '700' },
  actionTitle: { color: '#172219', fontSize: 18, fontWeight: '800' },
  actionArrow: { color: '#344736', fontSize: 11, fontWeight: '800' },
  disabledButton: { opacity: 0.48 },
  resultSection: { marginTop: 28, paddingTop: 18, borderTopWidth: 1, borderColor: '#344238' },
  resultHeading: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  resultTitle: { color: '#f2f4eb', fontSize: 17, fontWeight: '700', marginTop: 17 },
  resultMeta: { color: '#96a49a', fontSize: 11, marginTop: 4, marginBottom: 12 },
  resultBody: { color: '#cfdbcf', fontSize: 13, lineHeight: 21, fontVariant: ['tabular-nums'] },
  emptyResult: { color: '#8f9c91', fontSize: 13, marginTop: 18 },
  connectionSection: { paddingTop: 2 },
  inputLabel: { color: '#aab7aa', fontSize: 10, fontWeight: '700', marginTop: 21, marginBottom: 8 },
  input: { minHeight: 48, backgroundColor: '#1d2820', borderWidth: 1, borderColor: '#3a493d', color: '#f2f4eb', paddingHorizontal: 13, fontSize: 14 },
  connectButton: { minHeight: 50, alignItems: 'center', justifyContent: 'center', backgroundColor: '#c3f36b', marginTop: 22 },
  connectButtonText: { color: '#172219', fontSize: 12, fontWeight: '800' },
  statusMessage: { fontSize: 13, lineHeight: 19, marginTop: 15 },
  goodText: { color: '#c3f36b' },
  errorText: { color: '#ff9a7c' },
  mutedText: { color: '#aab7aa' },
  credentialNote: { color: '#87958a', fontSize: 11, lineHeight: 16, marginTop: 9 },
  footer: { flexDirection: 'row', justifyContent: 'space-between', gap: 12, borderTopWidth: 1, borderColor: '#344238', paddingTop: 14, marginTop: 30 },
  footerText: { color: '#87958a', fontSize: 9, fontWeight: '700' },
});