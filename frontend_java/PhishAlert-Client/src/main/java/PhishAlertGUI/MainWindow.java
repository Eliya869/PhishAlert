package PhishAlertGUI;

import javax.swing.*;
import javax.swing.border.EmptyBorder;
import javax.swing.border.TitledBorder;
import javax.swing.table.DefaultTableModel;
import java.awt.*;
import java.awt.geom.RoundRectangle2D;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;

public class MainWindow extends JFrame {

    // Modern Cyber Dark Theme Palette
    private final Color COLOR_BG = new Color(13, 15, 19);
    private final Color COLOR_CARD = new Color(21, 25, 32);
    private final Color COLOR_ACCENT = new Color(0, 210, 255);
    private final Color COLOR_TEXT = new Color(240, 240, 240);
    private final Color COLOR_SAFE = new Color(46, 213, 115);
    private final Color COLOR_SUSPICIOUS = new Color(255, 165, 2);
    private final Color COLOR_DANGER = new Color(255, 71, 87);

    private JTextField senderField;
    private JTextArea bodyArea;
    private RoundedButton scanButton;
    private JProgressBar riskMeter;

    // Real-Time Analytics Dashboard Labels
    private JLabel lblLevenshteinScore;
    private JLabel lblAiScore;
    private JLabel lblAuthStatus;
    private JLabel lblFinalDecision;

    private JPanel feedbackPanel;
    private JButton btnReportMistake;
    private String lastSender = "";
    private String lastClassification = "";

    public MainWindow() {
        setupWindow();
        initUI();
    }

    private void setupWindow() {
        setTitle("PhishAlert | Intelligent Email Security Dashboard");
        setSize(1150, 850);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        getContentPane().setBackground(COLOR_BG);
        setLayout(new BorderLayout());
    }

    private void initUI() {
        // --- TOP HEADER PANEL ---
        JPanel header = new JPanel(new BorderLayout());
        header.setBackground(COLOR_BG);
        header.setBorder(new EmptyBorder(25, 30, 10, 30));

        JPanel titlePanel = new JPanel(new BorderLayout());
        titlePanel.setBackground(COLOR_BG);

        JLabel title = new JLabel("PhishAlert Security Suite");
        title.setFont(new Font("Segoe UI", Font.BOLD, 28));
        title.setForeground(COLOR_ACCENT);

        JLabel subtitle = new JLabel("Hybrid Detection Engine: Combining Structural Brand Analysis & Machine Learning Models");
        subtitle.setForeground(Color.GRAY);
        subtitle.setFont(new Font("Segoe UI", Font.PLAIN, 13));
        titlePanel.add(title, BorderLayout.NORTH);
        titlePanel.add(subtitle, BorderLayout.SOUTH);

        // Top Navigation - Model Telemetry Triggers
        JPanel topActionPanel = new JPanel(new FlowLayout(FlowLayout.RIGHT, 12, 0));
        topActionPanel.setBackground(COLOR_BG);

        RoundedButton btnShowRF = new RoundedButton("Random Forest Stats");
        btnShowRF.setPreferredSize(new Dimension(180, 38));
        btnShowRF.addActionListener(e -> showMetricsPopup("Random Forest Model", 95.05, 91.23, 95.12, 14919, 101, 1474, 15339));

        RoundedButton btnShowLR = new RoundedButton("Logistic Regression Stats");
        btnShowLR.setPreferredSize(new Dimension(200, 38));
        btnShowLR.addActionListener(e -> showMetricsPopup("Logistic Regression Model", 54.22, 28.87, 40.01, 12407, 2613, 11959, 4854));

        topActionPanel.add(btnShowRF);
        topActionPanel.add(btnShowLR);

        header.add(titlePanel, BorderLayout.CENTER);
        header.add(topActionPanel, BorderLayout.EAST);
        add(header, BorderLayout.NORTH);

        // --- MAIN WORKSPACE SPLIT PANEL ---
        JPanel splitPanel = new JPanel(new GridLayout(1, 2, 25, 0));
        splitPanel.setBackground(COLOR_BG);
        splitPanel.setBorder(new EmptyBorder(10, 30, 10, 30));

        // ================= LEFT SIDE: USER INTERACTION CARD =================
        JPanel leftCard = createStyledCard();
        leftCard.setLayout(new BoxLayout(leftCard, BoxLayout.Y_AXIS));
        leftCard.setBorder(new EmptyBorder(25, 25, 25, 25));

        leftCard.add(createSectionLabel("SENDER EMAIL ADDRESS:"));
        senderField = createStyledTextField();
        leftCard.add(senderField);
        leftCard.add(Box.createVerticalStrut(15));

        leftCard.add(createSectionLabel("EMAIL CONTENT / BODY TEXT:"));
        bodyArea = new JTextArea(12, 20);
        bodyArea.setBackground(new Color(33, 39, 49));
        bodyArea.setForeground(Color.WHITE);
        bodyArea.setFont(new Font("Segoe UI", Font.PLAIN, 14));
        bodyArea.setLineWrap(true);
        bodyArea.setWrapStyleWord(true);

        JScrollPane scroll = new JScrollPane(bodyArea);
        scroll.setBorder(BorderFactory.createLineBorder(new Color(50, 60, 75)));
        leftCard.add(scroll);
        leftCard.add(Box.createVerticalStrut(20));

        scanButton = new RoundedButton("Scan Email");
        leftCard.add(scanButton);
        splitPanel.add(leftCard);

        // ================= RIGHT SIDE: MONITORING & LOGGING =================
        JPanel rightPanelWrapper = new JPanel(new GridLayout(2, 1, 0, 20));
        rightPanelWrapper.setBackground(COLOR_BG);

        // Real-Time Diagnostic Dashboard
        JPanel telemetryCard = createDashboardCard("Analysis Results & Indicators");
        telemetryCard.setLayout(new GridLayout(4, 1, 8, 8));

        lblLevenshteinScore = createTelemetryLabel("Domain Similarity Distance (Levenshtein): ", "Waiting for input...");
        lblAiScore = createTelemetryLabel("Machine Learning Phishing Probability: ", "Waiting for input...");
        lblAuthStatus = createTelemetryLabel("Email Authentication Status (SPF/DKIM): ", "Waiting for input...");
        lblFinalDecision = createTelemetryLabel("System Security Verdict: ", "Waiting for input...");

        telemetryCard.add(lblLevenshteinScore);
        telemetryCard.add(lblAiScore);
        telemetryCard.add(lblAuthStatus);
        telemetryCard.add(lblFinalDecision);
        rightPanelWrapper.add(telemetryCard);

        // Database Logs History Panel
        JPanel historyCard = createDashboardCard("Historical Scan History Logs (SQLite DB)");
        historyCard.setLayout(new BorderLayout());

        String[] columns = {"Timestamp", "Sender Address", "Threat Score", "Verdict"};
        DefaultTableModel tableModel = new DefaultTableModel(columns, 0);
        JTable historyTable = new JTable(tableModel);
        historyTable.setBackground(COLOR_CARD);
        historyTable.setForeground(COLOR_TEXT);
        historyTable.setRowHeight(24);
        historyTable.setFont(new Font("Segoe UI", Font.PLAIN, 12));

        JScrollPane tableScroll = new JScrollPane(historyTable);
        tableScroll.setBorder(BorderFactory.createEmptyBorder());
        historyCard.add(tableScroll, BorderLayout.CENTER);
        rightPanelWrapper.add(historyCard);

        splitPanel.add(rightPanelWrapper);
        add(splitPanel, BorderLayout.CENTER);

        // --- FOOTER SECURITY BAR ---
        JPanel footer = new JPanel();
        footer.setLayout(new BoxLayout(footer, BoxLayout.Y_AXIS));
        footer.setBackground(COLOR_BG);
        footer.setBorder(new EmptyBorder(15, 30, 25, 30));

        riskMeter = new JProgressBar(0, 100);
        riskMeter.setValue(0);
        riskMeter.setStringPainted(true);
        riskMeter.setFont(new Font("Segoe UI", Font.BOLD, 14));
        riskMeter.setString("System Ready - Standing by for email scanning");
        riskMeter.setForeground(Color.GRAY);
        riskMeter.setBackground(new Color(33, 39, 49));
        riskMeter.setMaximumSize(new Dimension(1090, 35));
        riskMeter.setAlignmentX(Component.CENTER_ALIGNMENT);

        feedbackPanel = new JPanel(new FlowLayout(FlowLayout.CENTER, 15, 0));
        feedbackPanel.setBackground(COLOR_BG);
        feedbackPanel.setVisible(false);

        JLabel feedbackTxt = new JLabel("Was this assessment incorrect?");
        feedbackTxt.setForeground(Color.GRAY);
        feedbackTxt.setFont(new Font("Segoe UI", Font.ITALIC, 13));

        btnReportMistake = new JButton("Report Incorrect Classification (Feedback Loop)");
        btnReportMistake.setBackground(COLOR_DANGER);
        btnReportMistake.setForeground(Color.WHITE);
        btnReportMistake.setFont(new Font("Segoe UI", Font.BOLD, 12));
        btnReportMistake.setFocusPainted(false);
        btnReportMistake.setCursor(new Cursor(Cursor.HAND_CURSOR));

        feedbackPanel.add(feedbackTxt);
        feedbackPanel.add(btnReportMistake);

        footer.add(riskMeter);
        footer.add(Box.createVerticalStrut(12));
        footer.add(feedbackPanel);
        add(footer, BorderLayout.SOUTH);

        // Button Event Actions
        scanButton.addActionListener(e -> runLiveScan(tableModel));
        btnReportMistake.addActionListener(e -> sendHumanOverride());

        // Initial database loading
        refreshLogs(tableModel);
    }

    // High-Fidelity Popup for Confusion Matrix and Performance Curves
    private void showMetricsPopup(String modelName, double acc, double rec, double f1, int tn, int fp, int fn, int tp) {
        JDialog dialog = new JDialog(this, modelName + " Complete Evaluation Profile", true);
        dialog.setSize(520, 420);
        dialog.setLocationRelativeTo(this);
        dialog.getContentPane().setBackground(COLOR_CARD);
        dialog.setLayout(new BorderLayout(15, 15));

        // Top Metrics Overview Panel
        JPanel metricsPanel = new JPanel(new GridLayout(1, 3, 10, 0));
        metricsPanel.setBackground(COLOR_CARD);
        metricsPanel.setBorder(new EmptyBorder(20, 20, 10, 20));

        metricsPanel.add(createMetricBlock("Accuracy Score", acc + "%"));
        metricsPanel.add(createMetricBlock("Recall Sensitivity", rec + "%"));
        metricsPanel.add(createMetricBlock("Balanced F1-Score", f1 + "%"));
        dialog.add(metricsPanel, BorderLayout.NORTH);

        // Highly Detailed Visual Confusion Matrix Grid
        JPanel matrixContainer = new JPanel(new BorderLayout());
        matrixContainer.setBackground(COLOR_CARD);
        matrixContainer.setBorder(new EmptyBorder(10, 25, 25, 25));

        JPanel grid = new JPanel(new GridLayout(3, 3, 5, 5));
        grid.setBackground(new Color(28, 34, 43));
        grid.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        // Row 1 Headers
        grid.add(new JLabel(""));
        grid.add(createMatrixHeaderLabel("Predicted SAFE"));
        grid.add(createMatrixHeaderLabel("Predicted PHISH"));

        // Row 2 Data (Actual Safe)
        grid.add(createMatrixHeaderLabel("Actual SAFE"));
        grid.add(createMatrixCell(tn + " (True Safe)", COLOR_SAFE));
        grid.add(createMatrixCell(fp + " (False Phish)", COLOR_DANGER));

        // Row 3 Data (Actual Phish)
        grid.add(createMatrixHeaderLabel("Actual PHISH"));
        grid.add(createMatrixCell(fn + " (False Safe)", COLOR_DANGER));
        grid.add(createMatrixCell(tp + " (True Phish)", COLOR_SAFE));

        matrixContainer.add(grid, BorderLayout.CENTER);
        dialog.add(matrixContainer, BorderLayout.CENTER);
        dialog.setVisible(true);
    }

    private JPanel createMetricBlock(String title, String val) {
        JPanel p = new JPanel(new BorderLayout());
        p.setBackground(new Color(33, 39, 49));
        p.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(new Color(50, 60, 75), 1),
                BorderFactory.createEmptyBorder(10, 10, 10, 10)
        ));

        JLabel tLbl = new JLabel(title, SwingConstants.CENTER);
        tLbl.setFont(new Font("Segoe UI", Font.PLAIN, 12));
        tLbl.setForeground(Color.LIGHT_GRAY);

        JLabel vLbl = new JLabel(val, SwingConstants.CENTER);
        vLbl.setFont(new Font("Segoe UI", Font.BOLD, 18));
        vLbl.setForeground(COLOR_ACCENT);

        p.add(tLbl, BorderLayout.NORTH);
        p.add(vLbl, BorderLayout.CENTER);
        return p;
    }

    private void runLiveScan(DefaultTableModel model) {
        String sender = senderField.getText().trim();
        String body = bodyArea.getText().trim();

        if (body.isEmpty()) {
            JOptionPane.showMessageDialog(this, "Please insert email body content to analyze.");
            return;
        }

        scanButton.setEnabled(false);
        feedbackPanel.setVisible(false);
        riskMeter.setValue(0);
        riskMeter.setString("Analyzing patterns and verifying signatures...");

        new Thread(() -> {
            try {
                JsonObject res = ApiService.analyzeEmail(sender, body);
                double score = res.get("phish_score").getAsDouble();
                String classification = res.get("classification").getAsString();
                double levScore = res.has("lev_score") ? res.get("lev_score").getAsDouble() : 0.0;
                double aiProb = res.has("ai_prob") ? res.get("ai_prob").getAsDouble() : score;
                String authCheck = res.has("auth_check") ? res.get("auth_check").getAsString() : "UNVERIFIED";

                SwingUtilities.invokeLater(() -> {
                    scanButton.setEnabled(true);
                    lastSender = sender;
                    lastClassification = classification;
                    int finalScoreInt = (int) score;
                    riskMeter.setValue(finalScoreInt);

                    lblLevenshteinScore.setText("<html><font color='#AAAAAA'>Domain Similarity Distance (Levenshtein): </font><b><font color='#00D2FF'>" + levScore + "</font></b></html>");
                    lblAiScore.setText("<html><font color='#AAAAAA'>Machine Learning Phishing Probability: </font><b><font color='#00D2FF'>" + aiProb + "%</font></b></html>");
                    lblAuthStatus.setText("<html><font color='#AAAAAA'>Email Authentication Status (SPF/DKIM): </font><b><font color='#2ED573'>" + authCheck + "</font></b></html>");

                    if (finalScoreInt < 45) {
                        lblFinalDecision.setText("<html><font color='#AAAAAA'>System Security Verdict: </font><b><font color='#2ED573'>SECURE / LEGITIMATE EMAIL</font></b></html>");
                        riskMeter.setForeground(COLOR_SAFE);
                        riskMeter.setString(finalScoreInt + "% - Safe Email Profile Verified");
                    } else if (finalScoreInt < 75) {
                        lblFinalDecision.setText("<html><font color='#AAAAAA'>System Security Verdict: </font><b><font color='#FFA502'>SUSPICIOUS ANOMALY DETECTED</font></b></html>");
                        riskMeter.setForeground(COLOR_SUSPICIOUS);
                        riskMeter.setString(finalScoreInt + "% - Elevated Security Risk Caution");
                    } else {
                        lblFinalDecision.setText("<html><font color='#AAAAAA'>System Security Verdict: </font><b><font color='#FF4757'>MALICIOUS PHISHING PAYLOAD INTERCEPTED</font></b></html>");
                        riskMeter.setForeground(COLOR_DANGER);
                        riskMeter.setString(finalScoreInt + "% - Warning: Phishing Attack Detected!");
                    }
                    feedbackPanel.setVisible(true);
                    refreshLogs(model);
                });
            } catch (Exception ex) {
                SwingUtilities.invokeLater(() -> {
                    scanButton.setEnabled(true);
                    riskMeter.setString("Connection Error: Python Backend Server Offline");
                    riskMeter.setForeground(COLOR_DANGER);
                });
            }
        }).start();
    }

    private void refreshLogs(DefaultTableModel model) {
        new Thread(() -> {
            try {
                JsonArray history = ApiService.getHistory();
                SwingUtilities.invokeLater(() -> {
                    model.setRowCount(0);
                    for (JsonElement element : history) {
                        JsonObject obj = element.getAsJsonObject();
                        model.addRow(new Object[]{
                                obj.get("scan_date").getAsString(),
                                obj.get("sender_email").getAsString(),
                                obj.get("phish_score").getAsString() + "%",
                                obj.get("classification").getAsString()
                        });
                    }
                });
            } catch (Exception ex) {
                System.out.println("Sync Error: " + ex.getMessage());
            }
        }).start();
    }

    private void sendHumanOverride() {
        String correctLabel = lastClassification.equalsIgnoreCase("Safe") ? "Phishing" : "Safe";
        new Thread(() -> {
            try {
                ApiService.sendFeedback(lastSender, correctLabel);
                SwingUtilities.invokeLater(() -> {
                    feedbackPanel.setVisible(false);
                    JOptionPane.showMessageDialog(this, "Feedback loop database updated successfully.");
                });
            } catch (Exception ex) {
                ex.printStackTrace();
            }
        }).start();
    }

    private JPanel createStyledCard() {
        JPanel p = new JPanel() {
            @Override
            protected void paintComponent(Graphics g) {
                Graphics2D g2 = (Graphics2D) g.create();
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                g2.setColor(COLOR_CARD);
                g2.fill(new RoundRectangle2D.Float(0, 0, getWidth(), getHeight(), 20, 20));
                g2.dispose();
            }
        };
        p.setOpaque(false);
        return p;
    }

    private JPanel createDashboardCard(String title) {
        JPanel p = createStyledCard();
        p.setBorder(BorderFactory.createTitledBorder(BorderFactory.createEmptyBorder(), title, TitledBorder.LEFT, TitledBorder.TOP, new Font("Segoe UI", Font.BOLD, 13), COLOR_ACCENT));
        return p;
    }

    private JLabel createSectionLabel(String t) {
        JLabel l = new JLabel(t);
        l.setForeground(COLOR_ACCENT);
        l.setFont(new Font("Segoe UI", Font.BOLD, 12));
        l.setBorder(new EmptyBorder(5, 0, 5, 0));
        return l;
    }

    private JLabel createTelemetryLabel(String prefix, String value) {
        JLabel l = new JLabel("<html><font color='#B0B0B0'>" + prefix + "</font><font color='#FFFFFF'><b>" + value + "</b></font></html>");
        l.setFont(new Font("Segoe UI", Font.PLAIN, 13));
        l.setBorder(new EmptyBorder(0, 10, 0, 10));
        return l;
    }

    private JLabel createMatrixHeaderLabel(String text) {
        JLabel l = new JLabel(text, SwingConstants.CENTER);
        l.setFont(new Font("Segoe UI", Font.BOLD, 12));
        l.setForeground(Color.LIGHT_GRAY);
        return l;
    }

    private JLabel createMatrixCell(String text, Color baseColor) {
        JLabel l = new JLabel(text, SwingConstants.CENTER);
        l.setFont(new Font("Segoe UI", Font.BOLD, 12));
        l.setForeground(Color.WHITE);
        l.setOpaque(true);
        l.setBackground(baseColor.darker().darker());
        l.setBorder(BorderFactory.createLineBorder(new Color(50, 60, 75), 1));
        return l;
    }

    private JTextField createStyledTextField() {
        JTextField tf = new JTextField();
        tf.setBackground(new Color(33, 39, 49));
        tf.setForeground(Color.WHITE);
        tf.setCaretColor(COLOR_ACCENT);
        tf.setFont(new Font("Segoe UI", Font.PLAIN, 14));
        tf.setBorder(BorderFactory.createCompoundBorder(BorderFactory.createLineBorder(new Color(50, 60, 75)), BorderFactory.createEmptyBorder(6, 10, 6, 10)));
        tf.setMaximumSize(new Dimension(Integer.MAX_VALUE, 38));
        return tf;
    }

    class RoundedButton extends JButton {
        public RoundedButton(String text) {
            super(text);
            setContentAreaFilled(false);
            setFocusPainted(false);
            setBorderPainted(false);
            setForeground(Color.WHITE);
            setFont(new Font("Segoe UI", Font.BOLD, 13));
            setCursor(new Cursor(Cursor.HAND_CURSOR));
        }

        @Override
        protected void paintComponent(Graphics g) {
            Graphics2D g2 = (Graphics2D) g.create();
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            g2.setColor(isEnabled() ? COLOR_ACCENT : Color.DARK_GRAY);
            g2.fill(new RoundRectangle2D.Float(0, 0, getWidth(), getHeight(), 15, 15));
            super.paintComponent(g);
            g2.dispose();
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> new MainWindow().setVisible(true));
    }
}