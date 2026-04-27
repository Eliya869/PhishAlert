package PhishAlertGUI;

import javax.swing.*;
import javax.swing.border.EmptyBorder;
import javax.swing.border.LineBorder;
import java.awt.*;
import java.awt.geom.RoundRectangle2D;

/**
 * PhishAlert MainWindow - Enhanced Week 12 Implementation
 * Includes: Graphical Risk Meter, Security Alerts, and Human-in-the-Loop Feedback.
 */
public class MainWindow extends JFrame {

    // Cyber Palette
    private final Color COLOR_BG = new Color(15, 15, 15);
    private final Color COLOR_CARD = new Color(28, 28, 28);
    private final Color COLOR_ACCENT = new Color(0, 210, 255);
    private final Color COLOR_TEXT = new Color(240, 240, 240);

    // Status Colors
    private final Color COLOR_SAFE = new Color(50, 255, 126);
    private final Color COLOR_SUSPICIOUS = new Color(255, 175, 64);
    private final Color COLOR_DANGER = new Color(255, 71, 87);

    private JTextField senderField;
    private JTextArea bodyArea;
    private RoundedButton scanButton;
    private JLabel statusLabel;
    private JProgressBar riskMeter;

    // --- Feedback Loop Components (Week 12) ---
    private JPanel feedbackPanel;
    private JButton btnReportMistake;
    private String lastSender = "";
    private String lastClassification = "";

    public MainWindow() {
        setupWindow();
        initUI();
    }

    private void setupWindow() {
        setTitle("PhishAlert | Advanced Security Engine");
        setSize(600, 850); // Slightly taller to fit feedback
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        getContentPane().setBackground(COLOR_BG);
        setLayout(new BorderLayout());
    }

    private void initUI() {
        // --- Header Section ---
        JPanel header = new JPanel(new BorderLayout());
        header.setBackground(COLOR_BG);
        header.setBorder(new EmptyBorder(30, 40, 10, 40));

        JLabel title = new JLabel("PhishAlert Project");
        title.setFont(new Font("Segoe UI", Font.BOLD, 26));
        title.setForeground(COLOR_ACCENT);

        JLabel subtitle = new JLabel("Identifying and monitoring phishing messages");
        subtitle.setForeground(Color.GRAY);
        subtitle.setFont(new Font("Segoe UI", Font.PLAIN, 14));

        header.add(title, BorderLayout.NORTH);
        header.add(subtitle, BorderLayout.SOUTH);
        add(header, BorderLayout.NORTH);

        // --- Main Content (The Card) ---
        JPanel centerWrapper = new JPanel(new BorderLayout());
        centerWrapper.setBackground(COLOR_BG);
        centerWrapper.setBorder(new EmptyBorder(10, 40, 10, 40));

        JPanel card = new JPanel() {
            @Override
            protected void paintComponent(Graphics g) {
                Graphics2D g2 = (Graphics2D) g.create();
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                g2.setColor(COLOR_CARD);
                g2.fill(new RoundRectangle2D.Float(0, 0, getWidth(), getHeight(), 30, 30));
                g2.dispose();
            }
        };
        card.setLayout(new BoxLayout(card, BoxLayout.Y_AXIS));
        card.setBorder(new EmptyBorder(30, 30, 30, 30));
        card.setOpaque(false);

        card.add(createLabel("SENDER ADDRESS:"));
        senderField = createStyledTextField();
        card.add(senderField);

        card.add(Box.createVerticalStrut(25));

        card.add(createLabel("EMAIL CONTENT (BODY):"));
        bodyArea = new JTextArea(10, 20);
        bodyArea.setBackground(new Color(45, 45, 45));
        bodyArea.setForeground(Color.WHITE);
        bodyArea.setCaretColor(COLOR_ACCENT);
        bodyArea.setFont(new Font("Consolas", Font.PLAIN, 14));
        bodyArea.setLineWrap(true);
        bodyArea.setWrapStyleWord(true);

        JScrollPane scroll = new JScrollPane(bodyArea);
        scroll.setBorder(BorderFactory.createLineBorder(new Color(60, 60, 60), 1));
        card.add(scroll);

        centerWrapper.add(card);
        add(centerWrapper, BorderLayout.CENTER);

        // --- Bottom Section ---
        JPanel footer = new JPanel();
        footer.setLayout(new BoxLayout(footer, BoxLayout.Y_AXIS));
        footer.setBackground(COLOR_BG);
        footer.setBorder(new EmptyBorder(10, 40, 40, 40));

        riskMeter = new JProgressBar(0, 100);
        riskMeter.setValue(0);
        riskMeter.setStringPainted(true);
        riskMeter.setFont(new Font("Segoe UI", Font.BOLD, 12));
        riskMeter.setForeground(Color.GRAY);
        riskMeter.setBackground(new Color(45, 45, 45));
        riskMeter.setBorder(new LineBorder(new Color(60, 60, 60)));
        riskMeter.setMaximumSize(new Dimension(520, 30));
        riskMeter.setAlignmentX(Component.CENTER_ALIGNMENT);

        scanButton = new RoundedButton("SCAN EMAIL");
        scanButton.setAlignmentX(Component.CENTER_ALIGNMENT);

        statusLabel = new JLabel("SYSTEM STATUS: STANDBY", SwingConstants.CENTER);
        statusLabel.setForeground(Color.GRAY);
        statusLabel.setFont(new Font("Monospaced", Font.BOLD, 13));
        statusLabel.setAlignmentX(Component.CENTER_ALIGNMENT);

        // --- Feedback Panel Setup ---
        feedbackPanel = new JPanel(new FlowLayout(FlowLayout.CENTER, 15, 0));
        feedbackPanel.setBackground(COLOR_BG);
        feedbackPanel.setVisible(false);

        JLabel feedbackTxt = new JLabel("Is this result accurate?");
        feedbackTxt.setForeground(Color.GRAY);
        feedbackTxt.setFont(new Font("Segoe UI", Font.ITALIC, 13));

        btnReportMistake = new JButton("Report Mistake");
        btnReportMistake.setFocusPainted(false);
        btnReportMistake.setBackground(COLOR_DANGER);
        btnReportMistake.setForeground(Color.WHITE);
        btnReportMistake.setCursor(new Cursor(Cursor.HAND_CURSOR));

        feedbackPanel.add(feedbackTxt);
        feedbackPanel.add(btnReportMistake);

        footer.add(riskMeter);
        footer.add(Box.createVerticalStrut(20));
        footer.add(scanButton);
        footer.add(Box.createVerticalStrut(15));
        footer.add(statusLabel);
        footer.add(Box.createVerticalStrut(15));
        footer.add(feedbackPanel);

        add(footer, BorderLayout.SOUTH);

        // Listeners
        scanButton.addActionListener(e -> triggerScan());
        btnReportMistake.addActionListener(e -> triggerFeedback());
    }

    private JLabel createLabel(String text) {
        JLabel l = new JLabel(text);
        l.setForeground(COLOR_ACCENT);
        l.setFont(new Font("Segoe UI", Font.BOLD, 12));
        l.setBorder(new EmptyBorder(0, 0, 8, 0));
        return l;
    }

    private JTextField createStyledTextField() {
        JTextField tf = new JTextField();
        tf.setBackground(new Color(45, 45, 45));
        tf.setForeground(Color.WHITE);
        tf.setCaretColor(COLOR_ACCENT);
        tf.setFont(new Font("Segoe UI", Font.PLAIN, 15));
        tf.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(new Color(60, 60, 60), 1),
                new EmptyBorder(8, 12, 8, 12)));
        tf.setMaximumSize(new Dimension(Integer.MAX_VALUE, 45));
        return tf;
    }

    private void triggerScan() {
        String sender = senderField.getText().trim();
        String body = bodyArea.getText().trim();

        if (body.isEmpty()) {
            JOptionPane.showMessageDialog(this, "Please enter email content before scanning.");
            return;
        }

        // UI Reset
        scanButton.setEnabled(false);
        feedbackPanel.setVisible(false);
        statusLabel.setText(">> ANALYZING PATTERNS...");
        statusLabel.setForeground(COLOR_ACCENT);
        riskMeter.setValue(0);

        new Thread(() -> {
            try {
                com.google.gson.JsonObject response = ApiService.analyzeEmail(sender, body);

                double score = response.get("phish_score").getAsDouble();
                String classification = response.get("classification").getAsString();

                SwingUtilities.invokeLater(() -> {
                    scanButton.setEnabled(true);
                    lastSender = sender;
                    lastClassification = classification;

                    int intScore = (int) score;
                    riskMeter.setValue(intScore);

                    if (intScore < 40) {
                        applyResult(COLOR_SAFE, "SECURE", intScore);
                    } else if (intScore < 70) {
                        applyResult(COLOR_SUSPICIOUS, "SUSPICIOUS", intScore);
                    } else {
                        applyResult(COLOR_DANGER, "PHISHING DETECTED", intScore);
                        showSecurityPopUp(score);
                    }

                    // Show feedback panel after results are in
                    feedbackPanel.setVisible(true);
                });

            } catch (Exception ex) {
                SwingUtilities.invokeLater(() -> {
                    scanButton.setEnabled(true);
                    statusLabel.setText(">> ERROR: API UNREACHABLE");
                    statusLabel.setForeground(Color.RED);
                });
            }
        }).start();
    }

    private void triggerFeedback() {
        // Determine the correction
        String correctLabel = lastClassification.equalsIgnoreCase("Safe") ? "Phishing" : "Safe";

        new Thread(() -> {
            try {
                ApiService.sendFeedback(lastSender, correctLabel);
                SwingUtilities.invokeLater(() -> {
                    feedbackPanel.setVisible(false);
                    JOptionPane.showMessageDialog(this, "Feedback recorded. The AI will learn from this correction.");
                });
            } catch (Exception ex) {
                ex.printStackTrace();
            }
        }).start();
    }

    private void applyResult(Color color, String status, int score) {
        statusLabel.setText(">> RESULT: " + status + " (" + score + "%)");
        statusLabel.setForeground(color);
        riskMeter.setForeground(color);
    }

    private void showSecurityPopUp(double score) {
        JOptionPane.showMessageDialog(this,
                "CRITICAL SECURITY WARNING\n\nHigh phishing risk detected (" + score + "%).",
                "Security Alert", JOptionPane.ERROR_MESSAGE);
    }

    class RoundedButton extends JButton {
        public RoundedButton(String text) {
            super(text);
            setContentAreaFilled(false);
            setFocusPainted(false);
            setBorderPainted(false);
            setForeground(Color.WHITE);
            setFont(new Font("Segoe UI", Font.BOLD, 15));
            setCursor(new Cursor(Cursor.HAND_CURSOR));
            setPreferredSize(new Dimension(520, 50));
            setMaximumSize(new Dimension(520, 50));
        }

        @Override
        protected void paintComponent(Graphics g) {
            Graphics2D g2 = (Graphics2D) g.create();
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            g2.setColor(isEnabled() ? COLOR_ACCENT : Color.DARK_GRAY);
            g2.fill(new RoundRectangle2D.Float(0, 0, getWidth(), getHeight(), 20, 20));
            super.paintComponent(g);
            g2.dispose();
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> new MainWindow().setVisible(true));
    }
}