package PhishAlertGUI;

import javax.swing.*;
import javax.swing.border.EmptyBorder;
import javax.swing.border.MatteBorder;
import javax.swing.table.DefaultTableCellRenderer;
import javax.swing.table.DefaultTableModel;
import javax.swing.table.JTableHeader;
import java.awt.*;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.awt.geom.RoundRectangle2D;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;

public class MainWindow extends JFrame {

    // Colors
    private final Color COLOR_BG = new Color(13, 15, 19);
    private final Color COLOR_NAV = new Color(20, 23, 29);
    private final Color COLOR_CARD = new Color(26, 30, 38);
    private final Color COLOR_PANEL_INNER = new Color(34, 39, 49);
    private final Color COLOR_BORDER = new Color(50, 58, 70);
    private final Color COLOR_ACCENT = new Color(0, 168, 255);
    private final Color COLOR_TEXT = new Color(230, 235, 240);
    private final Color COLOR_MUTED = new Color(140, 150, 160);

    private final Color COLOR_SAFE = new Color(46, 213, 115);
    private final Color COLOR_SUSPICIOUS = new Color(255, 165, 2);
    private final Color COLOR_DANGER = new Color(255, 71, 87);
    private final Color COLOR_PURPLE = new Color(155, 121, 255);

    // UI Elements
    private JTextField senderField;
    private JTextArea bodyArea;
    private RoundedButton scanButton;
    private RoundedButton btnReportMistake;
    private JProgressBar riskMeter;

    private JLabel lblFeatLinks;
    private JLabel lblFeatDomain;
    private JLabel lblFeatKeywords;

    private JLabel valLevenshtein;
    private JLabel valAiScore;
    private JLabel valDecision;

    private JPanel feedbackPanel;
    private JLabel feedbackTxt;
    private String lastSender = "";
    private String lastClassification = "";

    private JPanel cardPanel;
    private CardLayout cardLayout;

    private DefaultTableModel activeHistoryModel;
    private DefaultTableModel fullHistoryModel;

    private XAIRadarChart radarChart;

    public MainWindow() {
        setupWindow();
        initUI();
    }

    private void setupWindow() {
        setTitle("PhishAlert - Security Dashboard");
        setSize(1280, 960);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        getContentPane().setBackground(COLOR_BG);
        setLayout(new BorderLayout());

        UIManager.put("OptionPane.background", COLOR_CARD);
        UIManager.put("Panel.background", COLOR_CARD);
        UIManager.put("OptionPane.messageForeground", COLOR_TEXT);
    }

    private void initUI() {
        // --- HEADER ---
        JPanel topContainer = new JPanel(new BorderLayout());
        topContainer.setBackground(COLOR_NAV);

        JPanel header = new JPanel(new GridLayout(2, 1, 0, 5));
        header.setBackground(COLOR_NAV);
        header.setBorder(new EmptyBorder(25, 35, 15, 35));

        JLabel title = new JLabel("PhishAlert Dashboard");
        title.setFont(new Font("Segoe UI", Font.BOLD, 26));
        title.setForeground(Color.WHITE);

        JLabel subtitle = new JLabel("Smart Phishing Detection");
        subtitle.setForeground(COLOR_ACCENT);
        subtitle.setFont(new Font("Segoe UI", Font.BOLD, 14));

        header.add(title);
        header.add(subtitle);
        topContainer.add(header, BorderLayout.NORTH);

        // --- NAVIGATION ---
        JPanel navBar = new JPanel(new FlowLayout(FlowLayout.LEFT, 10, 0));
        navBar.setBackground(COLOR_NAV);
        navBar.setBorder(new MatteBorder(0, 0, 1, 0, COLOR_BORDER));

        JButton btnTab1 = createNavButton("Scan Window");
        JButton btnTab2 = createNavButton("Models Statistics");
        JButton btnTab3 = createNavButton("Scan History");
        JButton btnTab4 = createNavButton("Threat Radar");

        navBar.add(Box.createHorizontalStrut(25));
        navBar.add(btnTab1);
        navBar.add(btnTab2);
        navBar.add(btnTab3);
        navBar.add(btnTab4);

        topContainer.add(navBar, BorderLayout.SOUTH);
        add(topContainer, BorderLayout.NORTH);

        // --- WORKSPACE ---
        cardLayout = new CardLayout();
        cardPanel = new JPanel(cardLayout);
        cardPanel.setBackground(COLOR_BG);
        cardPanel.setBorder(new EmptyBorder(20, 20, 20, 20));

        cardPanel.add(createScannerTab(), "Scan Window");
        cardPanel.add(createStatisticsTab(), "Models Statistics");
        cardPanel.add(createDatabaseTab(), "Scan History");
        cardPanel.add(createXaiTab(), "Threat Radar");

        add(cardPanel, BorderLayout.CENTER);

        btnTab1.addActionListener(e -> { cardLayout.show(cardPanel, "Scan Window"); updateNavState(btnTab1, btnTab2, btnTab3, btnTab4); if(activeHistoryModel!=null) refreshLogs(activeHistoryModel); });
        btnTab2.addActionListener(e -> { cardLayout.show(cardPanel, "Models Statistics"); updateNavState(btnTab2, btnTab1, btnTab3, btnTab4); });
        btnTab3.addActionListener(e -> { cardLayout.show(cardPanel, "Scan History"); updateNavState(btnTab3, btnTab1, btnTab2, btnTab4); if (fullHistoryModel != null) refreshLogs(fullHistoryModel); });
        btnTab4.addActionListener(e -> { cardLayout.show(cardPanel, "Threat Radar"); updateNavState(btnTab4, btnTab1, btnTab2, btnTab3); });

        updateNavState(btnTab1, btnTab2, btnTab3, btnTab4);

        // --- FOOTER ---
        JPanel footer = new JPanel();
        footer.setLayout(new BoxLayout(footer, BoxLayout.Y_AXIS));
        footer.setBackground(COLOR_BG);
        footer.setBorder(new EmptyBorder(10, 35, 20, 35));

        riskMeter = new JProgressBar(0, 100);
        riskMeter.setValue(0);
        riskMeter.setStringPainted(true);
        riskMeter.setFont(new Font("Segoe UI", Font.BOLD, 14));
        riskMeter.setString("Ready to scan...");
        riskMeter.setForeground(Color.GRAY);
        riskMeter.setBackground(COLOR_CARD);
        riskMeter.setBorder(BorderFactory.createLineBorder(COLOR_BORDER, 1));
        riskMeter.setMaximumSize(new Dimension(1400, 35));
        riskMeter.setAlignmentX(Component.CENTER_ALIGNMENT);

        feedbackPanel = new JPanel(new FlowLayout(FlowLayout.CENTER, 15, 0));
        feedbackPanel.setBackground(COLOR_BG);
        feedbackPanel.setVisible(false);

        feedbackTxt = new JLabel("Wrong?");
        feedbackTxt.setForeground(COLOR_MUTED);
        feedbackTxt.setFont(new Font("Segoe UI", Font.PLAIN, 14));

        btnReportMistake = new RoundedButton("Fix Result");
        btnReportMistake.setBackground(COLOR_DANGER);
        btnReportMistake.setForeground(Color.WHITE);
        btnReportMistake.setFont(new Font("Segoe UI", Font.BOLD, 12));
        btnReportMistake.setPreferredSize(new Dimension(220, 35));

        feedbackPanel.add(feedbackTxt);
        feedbackPanel.add(btnReportMistake);

        footer.add(riskMeter);
        footer.add(Box.createVerticalStrut(15));
        footer.add(feedbackPanel);
        add(footer, BorderLayout.SOUTH);

        btnReportMistake.addActionListener(e -> sendHumanOverride());
    }

    private JButton createNavButton(String text) {
        JButton btn = new JButton(text);
        btn.setFont(new Font("Segoe UI", Font.BOLD, 14));
        btn.setForeground(COLOR_MUTED);
        btn.setBackground(COLOR_NAV);
        btn.setFocusPainted(false);
        btn.setBorderPainted(false);
        btn.setContentAreaFilled(false);
        btn.setOpaque(true);
        btn.setCursor(new Cursor(Cursor.HAND_CURSOR));
        btn.setBorder(new EmptyBorder(12, 20, 12, 20));

        btn.addMouseListener(new MouseAdapter() {
            public void mouseEntered(MouseEvent evt) {
                if(btn.getForeground() != COLOR_ACCENT) btn.setBackground(COLOR_CARD);
            }
            public void mouseExited(MouseEvent evt) {
                if(btn.getForeground() != COLOR_ACCENT) btn.setBackground(COLOR_NAV);
            }
        });
        return btn;
    }

    private void updateNavState(JButton active, JButton... inactive) {
        active.setForeground(COLOR_ACCENT);
        active.setBackground(COLOR_BG);
        active.setBorder(new MatteBorder(3, 1, 0, 1, COLOR_BORDER));
        for (JButton b : inactive) {
            b.setForeground(COLOR_MUTED);
            b.setBackground(COLOR_NAV);
            b.setBorder(new EmptyBorder(12, 20, 12, 20));
        }
    }

    // ==========================================
    // TAB 1: SCANNER
    // ==========================================
    private JPanel createScannerTab() {
        JPanel panel = new JPanel(new GridLayout(1, 2, 25, 0));
        panel.setBackground(COLOR_BG);

        // LEFT SIDE
        JPanel leftCard = createDashboardCard("Email Details");
        leftCard.setLayout(new BoxLayout(leftCard, BoxLayout.Y_AXIS));

        leftCard.add(createSectionLabel("Sender Address:"));
        senderField = createStyledTextField();
        senderField.setAlignmentX(Component.LEFT_ALIGNMENT);
        leftCard.add(senderField);
        leftCard.add(Box.createVerticalStrut(20));

        leftCard.add(createSectionLabel("Email Text:"));
        bodyArea = new JTextArea();
        bodyArea.setBackground(COLOR_PANEL_INNER);
        bodyArea.setForeground(Color.WHITE);
        bodyArea.setFont(new Font("Segoe UI", Font.PLAIN, 15));
        bodyArea.setCaretColor(COLOR_ACCENT);
        bodyArea.setLineWrap(true);
        bodyArea.setWrapStyleWord(true);
        bodyArea.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        JScrollPane scroll = styleScrollPane(new JScrollPane(bodyArea));
        scroll.setAlignmentX(Component.LEFT_ALIGNMENT);
        scroll.setPreferredSize(new Dimension(Integer.MAX_VALUE, 300));
        leftCard.add(scroll);
        leftCard.add(Box.createVerticalStrut(20));

        leftCard.add(createSectionLabel("Quick Checks:"));
        JPanel featureGrid = new JPanel(new GridLayout(1, 3, 15, 0));
        featureGrid.setBackground(COLOR_CARD);
        featureGrid.setAlignmentX(Component.LEFT_ALIGNMENT);

        lblFeatLinks = createDynamicValueLabel("-", COLOR_TEXT);
        lblFeatDomain = createDynamicValueLabel("-", COLOR_TEXT);
        lblFeatKeywords = createDynamicValueLabel("-", COLOR_TEXT);

        featureGrid.add(createFeatureBlock("Has Links?", lblFeatLinks));
        featureGrid.add(createFeatureBlock("Brand Fake Check", lblFeatDomain));
        featureGrid.add(createFeatureBlock("Panic Words", lblFeatKeywords));

        featureGrid.setMaximumSize(new Dimension(Integer.MAX_VALUE, 75));
        leftCard.add(featureGrid);
        leftCard.add(Box.createVerticalStrut(25));

        scanButton = new RoundedButton("Scan Email");
        scanButton.setBackground(COLOR_ACCENT);
        scanButton.setAlignmentX(Component.LEFT_ALIGNMENT);
        scanButton.setMaximumSize(new Dimension(Integer.MAX_VALUE, 50));
        scanButton.setFont(new Font("Segoe UI", Font.BOLD, 16));
        leftCard.add(scanButton);

        panel.add(leftCard);

        // RIGHT SIDE
        JPanel rightWrapper = new JPanel(new GridLayout(2, 1, 0, 20));
        rightWrapper.setBackground(COLOR_BG);

        JPanel telemetryCard = createDashboardCard("Scan Results");
        telemetryCard.setLayout(new BorderLayout());

        JPanel heroPanel = new JPanel(new BorderLayout());
        heroPanel.setBackground(COLOR_CARD);
        heroPanel.setBorder(new MatteBorder(0, 0, 1, 0, COLOR_BORDER));

        JLabel heroTitle = new JLabel("FINAL DECISION", SwingConstants.CENTER);
        heroTitle.setForeground(COLOR_MUTED);
        heroTitle.setFont(new Font("Segoe UI", Font.BOLD, 13));
        heroTitle.setBorder(new EmptyBorder(15, 0, 5, 0));

        valDecision = new JLabel("WAITING", SwingConstants.CENTER);
        valDecision.setFont(new Font("Segoe UI", Font.BOLD, 32));
        valDecision.setForeground(COLOR_MUTED);
        valDecision.setBorder(new EmptyBorder(0, 0, 20, 0));

        heroPanel.add(heroTitle, BorderLayout.NORTH);
        heroPanel.add(valDecision, BorderLayout.CENTER);
        telemetryCard.add(heroPanel, BorderLayout.NORTH);

        JPanel detailsPanel = new JPanel(new GridLayout(2, 1, 0, 0));
        detailsPanel.setBackground(COLOR_CARD);
        valLevenshtein = createDynamicValueLabel("-", COLOR_ACCENT);
        valAiScore = createDynamicValueLabel("-", COLOR_ACCENT);

        detailsPanel.add(createResultRow("Fake Brand Score", valLevenshtein));
        detailsPanel.add(createResultRow("AI Danger Score", valAiScore));
        telemetryCard.add(detailsPanel, BorderLayout.CENTER);

        rightWrapper.add(telemetryCard);

        JPanel shortHistoryCard = createDashboardCard("Recent Scans");
        shortHistoryCard.setLayout(new BorderLayout());

        String[] shortCols = {"Time", "Sender", "Threat Score", "Status"};
        activeHistoryModel = new DefaultTableModel(shortCols, 0);
        JTable shortTable = styleZebraTable(new JTable(activeHistoryModel));
        JScrollPane shortScroll = styleScrollPane(new JScrollPane(shortTable));

        shortHistoryCard.add(shortScroll, BorderLayout.CENTER);
        rightWrapper.add(shortHistoryCard);

        panel.add(rightWrapper);

        scanButton.addActionListener(e -> runLiveScan());
        refreshLogs(activeHistoryModel);

        return panel;
    }

    // ==========================================
    // TAB 2: STATISTICS
    // ==========================================
    private JPanel createStatisticsTab() {
        JPanel panel = new JPanel(new BorderLayout(0, 16));
        panel.setBackground(COLOR_BG);

        JPanel header = new JPanel(new BorderLayout());
        header.setBackground(COLOR_BG);

        JLabel title = new JLabel("Model Performance");
        title.setFont(new Font("Segoe UI", Font.BOLD, 22));
        title.setForeground(Color.WHITE);

        JLabel subtitle = new JLabel("Metrics & Graphs ");
        subtitle.setFont(new Font("Segoe UI", Font.BOLD, 13));
        subtitle.setForeground(COLOR_MUTED);

        JPanel titleStack = new JPanel(new GridLayout(2, 1, 0, 4));
        titleStack.setOpaque(false);
        titleStack.add(title);
        titleStack.add(subtitle);
        header.add(titleStack, BorderLayout.WEST);
        panel.add(header, BorderLayout.NORTH);

        JPanel modelGrid = new JPanel(new GridLayout(1, 2, 18, 0));
        modelGrid.setBackground(COLOR_BG);
        modelGrid.add(createLogisticRegressionPanel());
        modelGrid.add(createRandomForestPanel());
        panel.add(modelGrid, BorderLayout.CENTER);

        JPanel bottom = new JPanel(new GridLayout(1, 3, 14, 0));
        bottom.setBackground(COLOR_BG);
        bottom.add(createThresholdPanel());
        bottom.add(createDataSplitPanel());
        bottom.add(createDeploymentPanel());
        panel.add(bottom, BorderLayout.SOUTH);

        return panel;
    }

    private JPanel createLogisticRegressionPanel() {
        JPanel card = createDashboardCard("Logistic Regression (Weight: 30%)");
        card.setLayout(new BorderLayout(0, 12));

        JPanel top = new JPanel(new BorderLayout(12, 0));
        top.setOpaque(false);
        top.add(createMetricSummary(new String[][]{
                {"Accuracy", "90.81%", "91"},
                {"Precision", "89.68%", "90"},
                {"Recall", "93.36%", "93"},
                {"F1 Score", "91.48%", "91"}
        }), BorderLayout.CENTER);
        top.add(createStatusPill("High Stability", COLOR_SAFE), BorderLayout.EAST);
        card.add(top, BorderLayout.NORTH);

        JPanel center = new JPanel(new GridLayout(1, 2, 12, 0));
        center.setOpaque(false);
        center.add(createBarChartPanel("Core Metrics", new String[]{"Acc", "Prec", "Recall", "F1"},
                new int[]{91, 90, 93, 91},
                new Color[]{COLOR_SAFE, COLOR_SAFE, COLOR_SAFE, COLOR_ACCENT}));
        center.add(createGradientDescentPanel());
        card.add(center, BorderLayout.CENTER);

        JPanel bottom = new JPanel(new GridLayout(1, 2, 10, 0));
        bottom.setOpaque(false);
        bottom.add(createBeautifulConfusionMatrix(13213, 1807, 1117, 15696));
        bottom.add(createMiniCurvePanel("ROC / PR Curve", new int[]{20, 45, 68, 85, 93, 96, 98}, new int[]{15, 38, 62, 80, 90, 95, 97}, COLOR_ACCENT, COLOR_PURPLE));
        card.add(bottom, BorderLayout.SOUTH);
        return card;
    }

    private JPanel createRandomForestPanel() {
        JPanel card = createDashboardCard("Random Forest (Weight: 70%)");
        card.setLayout(new BorderLayout(0, 12));

        JPanel top = new JPanel(new BorderLayout(12, 0));
        top.setOpaque(false);
        top.add(createMetricSummary(new String[][]{
                {"Accuracy", "91.08%", "91"},
                {"Precision", "89.59%", "90"},
                {"Recall", "94.02%", "94"},
                {"F1 Score", "91.75%", "92"}
        }), BorderLayout.CENTER);
        top.add(createStatusPill("Primary Engine", COLOR_ACCENT), BorderLayout.EAST);
        card.add(top, BorderLayout.NORTH);

        JPanel center = new JPanel(new GridLayout(1, 2, 12, 0));
        center.setOpaque(false);
        center.add(createBarChartPanel("Core Metrics", new String[]{"Acc", "Prec", "Recall", "F1"},
                new int[]{91, 90, 94, 92},
                new Color[]{COLOR_SAFE, COLOR_SAFE, COLOR_SAFE, COLOR_ACCENT}));
        center.add(createHorizontalBarChart("Feature Importance", new String[]{"Domain Match", "Security", "Has Links", "Auth"}, new int[]{92, 85, 60, 45}));
        card.add(center, BorderLayout.CENTER);

        JPanel bottom = new JPanel(new GridLayout(1, 2, 10, 0));
        bottom.setOpaque(false);
        bottom.add(createBeautifulConfusionMatrix(13184, 1836, 1005, 15808));
        bottom.add(createMiniCurvePanel("ROC / PR Curve", new int[]{22, 48, 70, 86, 94, 97, 99}, new int[]{18, 42, 65, 83, 92, 96, 98}, COLOR_ACCENT, COLOR_PURPLE));
        card.add(bottom, BorderLayout.SOUTH);
        return card;
    }

    private JPanel createThresholdPanel() {
        JPanel panel = createMiniCard("Risk Levels");
        panel.setLayout(new GridLayout(3, 1, 0, 8));
        panel.add(createInlineMetric("Safe", "0% - 44%", COLOR_SAFE));
        panel.add(createInlineMetric("Suspicious", "45% - 74%", COLOR_SUSPICIOUS));
        panel.add(createInlineMetric("Dangerous", "75% - 100%", COLOR_DANGER));
        return panel;
    }

    private JPanel createDataSplitPanel() {
        JPanel panel = createMiniCard("Data Setup");
        panel.setLayout(new GridLayout(3, 1, 0, 8));
        panel.add(createInlineMetric("Train / Test", "80% / 20%", COLOR_ACCENT));
        panel.add(createInlineMetric("Cross Validation", "3 Folds", COLOR_PURPLE));
        panel.add(createInlineMetric("Balancing", "50/50 Strategy", COLOR_SAFE));
        return panel;
    }

    private JPanel createDeploymentPanel() {
        JPanel panel = createMiniCard("System Status");
        panel.setLayout(new GridLayout(3, 1, 0, 8));
        panel.add(createInlineMetric("Calibration", "Optimized", COLOR_SAFE));
        panel.add(createInlineMetric("Drift Monitoring", "Enabled", COLOR_SAFE));
        panel.add(createInlineMetric("Feedback Loop", "Active Sync", COLOR_ACCENT));
        return panel;
    }

    private JPanel createMetricSummary(String[][] metrics) {
        JPanel panel = new JPanel(new GridLayout(1, metrics.length, 8, 0));
        panel.setOpaque(false);
        for (String[] metric : metrics) {
            int score = Integer.parseInt(metric[2]);
            Color color = score >= 80 ? COLOR_SAFE : score >= 50 ? COLOR_SUSPICIOUS : COLOR_DANGER;
            panel.add(createSmallMetric(metric[0], metric[1], color));
        }
        return panel;
    }

    private JLabel createStatusPill(String text, Color color) {
        JLabel label = new JLabel(text, SwingConstants.CENTER);
        label.setOpaque(true);
        label.setBackground(new Color(color.getRed(), color.getGreen(), color.getBlue(), 40));
        label.setForeground(color);
        label.setFont(new Font("Segoe UI", Font.BOLD, 12));
        label.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(color.darker()),
                new EmptyBorder(8, 12, 8, 12)
        ));
        label.setPreferredSize(new Dimension(145, 40));
        return label;
    }

    private JPanel createSmallMetric(String title, String value, Color color) {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBackground(COLOR_PANEL_INNER);
        panel.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(COLOR_BORDER),
                new EmptyBorder(10, 12, 10, 12)
        ));
        JLabel titleLabel = new JLabel(title);
        titleLabel.setForeground(COLOR_MUTED);
        titleLabel.setFont(new Font("Segoe UI", Font.BOLD, 11));

        JLabel valueLabel = new JLabel(value);
        valueLabel.setForeground(color);
        valueLabel.setFont(new Font("Segoe UI", Font.BOLD, 20));

        panel.add(titleLabel, BorderLayout.NORTH);
        panel.add(valueLabel, BorderLayout.CENTER);
        return panel;
    }

    private JPanel createInlineMetric(String label, String value, Color color) {
        JPanel row = new JPanel(new BorderLayout());
        row.setOpaque(false);
        JLabel left = new JLabel(label);
        left.setForeground(COLOR_MUTED);
        left.setFont(new Font("Segoe UI", Font.BOLD, 12));
        JLabel right = new JLabel(value);
        right.setForeground(color);
        right.setFont(new Font("Segoe UI", Font.BOLD, 12));
        row.add(left, BorderLayout.WEST);
        row.add(right, BorderLayout.EAST);
        return row;
    }

    private JPanel createMiniCard(String title) {
        JPanel panel = new JPanel();
        panel.setBackground(COLOR_PANEL_INNER);
        javax.swing.border.TitledBorder titledBorder = BorderFactory.createTitledBorder(
                BorderFactory.createLineBorder(COLOR_BORDER), title);
        titledBorder.setTitleFont(new Font("Segoe UI", Font.BOLD, 13));
        titledBorder.setTitleColor(Color.WHITE);
        panel.setBorder(BorderFactory.createCompoundBorder(titledBorder, new EmptyBorder(12, 14, 12, 14)));
        return panel;
    }

    private JPanel createBeautifulConfusionMatrix(int tn, int fp, int fn, int tp) {
        JPanel wrapper = createMiniCard("Confusion matrix");
        wrapper.setLayout(new BorderLayout(0, 8));
        JPanel grid = new JPanel(new GridLayout(3, 3, 3, 3));
        grid.setBackground(COLOR_PANEL_INNER);

        grid.add(new JLabel(""));
        grid.add(createMatrixHeader("Pred Safe"));
        grid.add(createMatrixHeader("Pred Threat"));
        grid.add(createMatrixHeader("Act Safe"));
        grid.add(createMatrixCell(String.valueOf(tn), "TN", COLOR_SAFE));
        grid.add(createMatrixCell(String.valueOf(fp), "FP", COLOR_SUSPICIOUS));
        grid.add(createMatrixHeader("Act Threat"));
        grid.add(createMatrixCell(String.valueOf(fn), "FN", COLOR_DANGER));
        grid.add(createMatrixCell(String.valueOf(tp), "TP", COLOR_SAFE));

        wrapper.add(grid, BorderLayout.CENTER);
        return wrapper;
    }

    private JLabel createMatrixHeader(String text) {
        JLabel label = new JLabel(text, SwingConstants.CENTER);
        label.setOpaque(true);
        label.setBackground(COLOR_CARD);
        label.setForeground(COLOR_MUTED);
        label.setFont(new Font("Segoe UI", Font.BOLD, 10));
        label.setBorder(BorderFactory.createLineBorder(COLOR_BORDER));
        return label;
    }

    private JPanel createMatrixCell(String value, String label, Color color) {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBackground(COLOR_CARD);
        panel.setBorder(BorderFactory.createLineBorder(color.darker()));

        JLabel main = new JLabel(value, SwingConstants.CENTER);
        main.setFont(new Font("Segoe UI", Font.BOLD, 18));
        main.setForeground(Color.WHITE);

        JLabel sub = new JLabel(label, SwingConstants.CENTER);
        sub.setFont(new Font("Segoe UI", Font.BOLD, 10));
        sub.setForeground(color);
        sub.setBorder(new EmptyBorder(0, 0, 5, 0));

        panel.add(main, BorderLayout.CENTER);
        panel.add(sub, BorderLayout.SOUTH);
        return panel;
    }

    private JPanel createGradientDescentPanel() {
        JPanel panel = createMiniCard("Learning Progress");
        panel.setLayout(new BorderLayout(0, 10));

        JPanel chart = new JPanel() {
            @Override
            protected void paintComponent(Graphics g) {
                super.paintComponent(g);
                Graphics2D g2 = (Graphics2D) g.create();
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                int w = getWidth(), h = getHeight();
                int left = 16, bottom = h - 18;
                g2.setColor(COLOR_BORDER);
                g2.drawLine(left, 12, left, bottom);
                g2.drawLine(left, bottom, w - 12, bottom);

                int[] losses = {86, 60, 42, 30, 22, 18, 14, 11, 9, 8};
                int prevX = left;
                int prevY = bottom - losses[0] * (h - 38) / 100;
                g2.setStroke(new BasicStroke(3f));
                g2.setColor(COLOR_ACCENT);
                for (int i = 1; i < losses.length; i++) {
                    int x = left + i * (w - left - 18) / (losses.length - 1);
                    int y = bottom - losses[i] * (h - 38) / 100;
                    g2.drawLine(prevX, prevY, x, y);
                    g2.fillOval(x - 3, y - 3, 6, 6);
                    prevX = x; prevY = y;
                }
                g2.dispose();
            }
        };
        chart.setBackground(COLOR_PANEL_INNER);
        chart.setPreferredSize(new Dimension(180, 118));

        JPanel labels = new JPanel(new GridLayout(1, 2, 8, 0));
        labels.setOpaque(false);
        labels.add(createInlineMetric("Start Error", "0.86", COLOR_SUSPICIOUS));
        labels.add(createInlineMetric("Final Error", "0.08", COLOR_SAFE));

        panel.add(chart, BorderLayout.CENTER);
        panel.add(labels, BorderLayout.SOUTH);
        return panel;
    }

    private JPanel createBarChartPanel(String title, String[] labels, int[] values, Color[] colors) {
        JPanel panel = createMiniCard(title);
        panel.setLayout(new BorderLayout());
        panel.add(new BarChart(labels, values, colors), BorderLayout.CENTER);
        return panel;
    }

    private JPanel createHorizontalBarChart(String title, String[] labels, int[] values) {
        JPanel panel = createMiniCard(title);
        panel.setLayout(new BorderLayout());
        panel.add(new HorizontalBarChart(labels, values), BorderLayout.CENTER);
        return panel;
    }

    private JPanel createMiniCurvePanel(String title, int[] rocValues, int[] prValues, Color rocColor, Color prColor) {
        JPanel panel = createMiniCard(title);
        panel.setLayout(new BorderLayout(0, 8));
        panel.add(new CurveChart(rocValues, prValues, rocColor, prColor), BorderLayout.CENTER);

        JPanel legend = new JPanel(new FlowLayout(FlowLayout.CENTER, 14, 0));
        legend.setOpaque(false);
        JLabel l1 = new JLabel("ROC"); l1.setForeground(rocColor); l1.setFont(new Font("Segoe UI", Font.BOLD, 11));
        JLabel l2 = new JLabel("PR"); l2.setForeground(prColor); l2.setFont(new Font("Segoe UI", Font.BOLD, 11));
        legend.add(l1);
        legend.add(l2);
        panel.add(legend, BorderLayout.SOUTH);
        return panel;
    }

    // --- Inner Chart Classes ---
    private class BarChart extends JPanel {
        private final String[] labels;
        private final int[] values;
        private final Color[] colors;

        BarChart(String[] labels, int[] values, Color[] colors) {
            this.labels = labels; this.values = values; this.colors = colors;
            setOpaque(false);
            setPreferredSize(new Dimension(220, 160));
        }

        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2 = (Graphics2D) g.create();
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            int w = getWidth(), h = getHeight();
            int top = 14, bottom = h - 28, left = 28;
            int usableW = Math.max(1, w - left - 14);
            int barGap = 12;
            int barW = Math.max(14, (usableW - barGap * (values.length - 1)) / values.length);

            g2.setColor(COLOR_BORDER); g2.setStroke(new BasicStroke(1f));
            g2.drawLine(left, top, left, bottom); g2.drawLine(left, bottom, w - 10, bottom);

            for (int i = 0; i < values.length; i++) {
                int x = left + i * (barW + barGap);
                int barH = values[i] * (bottom - top) / 100;
                int y = bottom - barH;
                g2.setColor(colors[i]);
                g2.fillRoundRect(x, y, barW, barH, 8, 8);
                g2.setColor(COLOR_TEXT);
                g2.setFont(new Font("Segoe UI", Font.BOLD, 10));
                g2.drawString(String.valueOf(values[i]), x + (barW - g2.getFontMetrics().stringWidth(String.valueOf(values[i]))) / 2, y - 4);
                g2.setColor(COLOR_MUTED);
                g2.drawString(labels[i], x + (barW - g2.getFontMetrics().stringWidth(labels[i])) / 2, bottom + 16);
            }
            g2.dispose();
        }
    }

    private class HorizontalBarChart extends JPanel {
        private final String[] labels;
        private final int[] values;

        HorizontalBarChart(String[] labels, int[] values) {
            this.labels = labels; this.values = values;
            setOpaque(false);
            setPreferredSize(new Dimension(220, 160));
        }

        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2 = (Graphics2D) g.create();
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            int labelW = 75, rowH = Math.max(22, getHeight() / labels.length);
            int barMaxW = Math.max(1, getWidth() - labelW - 42);

            g2.setFont(new Font("Segoe UI", Font.BOLD, 11));
            for (int i = 0; i < labels.length; i++) {
                int y = i * rowH + 8;
                int barW = values[i] * barMaxW / 100;
                g2.setColor(COLOR_MUTED);
                g2.drawString(labels[i], 2, y + 13);
                g2.setColor(COLOR_CARD);
                g2.fillRoundRect(labelW, y, barMaxW, 12, 8, 8);
                g2.setColor(i == 0 ? COLOR_SAFE : COLOR_ACCENT);
                g2.fillRoundRect(labelW, y, barW, 12, 8, 8);
                g2.setColor(COLOR_TEXT);
                g2.drawString(values[i] + "%", labelW + barMaxW + 8, y + 12);
            }
            g2.dispose();
        }
    }

    private class CurveChart extends JPanel {
        private final int[] first, second;
        private final Color c1, c2;

        CurveChart(int[] first, int[] second, Color c1, Color c2) {
            this.first = first; this.second = second; this.c1 = c1; this.c2 = c2;
            setOpaque(false);
            setPreferredSize(new Dimension(220, 130));
        }

        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2 = (Graphics2D) g.create();
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            int left = 24, top = 12, right = getWidth() - 12, bottom = getHeight() - 18;
            g2.setColor(COLOR_BORDER); g2.setStroke(new BasicStroke(1f));
            g2.drawLine(left, top, left, bottom); g2.drawLine(left, bottom, right, bottom);

            drawCurve(g2, first, c1, left, top, right, bottom);
            drawCurve(g2, second, c2, left, top, right, bottom);
            g2.dispose();
        }

        private void drawCurve(Graphics2D g2, int[] vals, Color c, int l, int t, int r, int b) {
            g2.setStroke(new BasicStroke(3f, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND));
            g2.setColor(c);
            int prevX = l, prevY = b - vals[0] * (b - t) / 100;
            for (int i = 1; i < vals.length; i++) {
                int x = l + i * (r - l) / (vals.length - 1);
                int y = b - vals[i] * (b - t) / 100;
                g2.drawLine(prevX, prevY, x, y);
                g2.fillOval(x - 3, y - 3, 6, 6);
                prevX = x; prevY = y;
            }
        }
    }

    // ==========================================
    // TAB 3: DATABASE
    // ==========================================
    private JPanel createDatabaseTab() {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBackground(COLOR_BG);

        JPanel mainLedgerCard = createDashboardCard("All Scan History");
        mainLedgerCard.setLayout(new BorderLayout());

        String[] cols = {"Time", "Sender", "Threat Score", "Final Verdict"};
        fullHistoryModel = new DefaultTableModel(cols, 0);
        JTable fullTable = styleZebraTable(new JTable(fullHistoryModel));
        JScrollPane scroll = styleScrollPane(new JScrollPane(fullTable));

        mainLedgerCard.add(scroll, BorderLayout.CENTER);
        panel.add(mainLedgerCard, BorderLayout.CENTER);

        refreshLogs(fullHistoryModel);
        return panel;
    }

    // ==========================================
    // TAB 4: THREAT RADAR
    // ==========================================
    private JPanel createXaiTab() {
        JPanel panel = new JPanel(new BorderLayout(20, 20));
        panel.setBackground(COLOR_BG);

        // Header
        JPanel header = new JPanel(new BorderLayout());
        header.setBackground(COLOR_BG);
        JLabel title = new JLabel("Threat Radar");
        title.setFont(new Font("Segoe UI", Font.BOLD, 22));
        title.setForeground(Color.WHITE);
        JLabel subtitle = new JLabel("Visual map that shows each feature found in the email.");
        subtitle.setFont(new Font("Segoe UI", Font.BOLD, 13));
        subtitle.setForeground(COLOR_MUTED);
        JPanel titleStack = new JPanel(new GridLayout(2, 1, 0, 4));
        titleStack.setOpaque(false);
        titleStack.add(title);
        titleStack.add(subtitle);
        header.add(titleStack, BorderLayout.WEST);
        panel.add(header, BorderLayout.NORTH);

        // Radar Card
        JPanel radarCard = createDashboardCard("Threat Breakdown");
        radarCard.setLayout(new BorderLayout());

        radarChart = new XAIRadarChart();
        radarCard.add(radarChart, BorderLayout.CENTER);

        // Explanations Panel
        JPanel infoPanel = new JPanel(new GridLayout(5, 1, 0, 10));
        infoPanel.setOpaque(false);
        infoPanel.setBorder(new EmptyBorder(20, 40, 20, 20));
        infoPanel.add(createXaiLegend("Fake Brand Name", "Looks like a famous brand but has a typo.", COLOR_DANGER));
        infoPanel.add(createXaiLegend("Panic Words", "Uses words like 'Urgent' or 'Suspend' to scare you.", COLOR_SUSPICIOUS));
        infoPanel.add(createXaiLegend("Bad Links", "Links point to suspicious places or hide IP addresses.", COLOR_ACCENT));
        infoPanel.add(createXaiLegend("Fake Sender", "The email address doesn't match the real company.", COLOR_PURPLE));
        infoPanel.add(createXaiLegend("Hidden Code", "Contains hidden HTML or weird text formatting.", COLOR_SAFE));

        radarCard.add(infoPanel, BorderLayout.EAST);
        panel.add(radarCard, BorderLayout.CENTER);

        return panel;
    }

    private JPanel createXaiLegend(String title, String desc, Color dotColor) {
        JPanel p = new JPanel(new BorderLayout(10, 0));
        p.setOpaque(false);

        JPanel dot = new JPanel() {
            @Override
            protected void paintComponent(Graphics g) {
                Graphics2D g2 = (Graphics2D)g;
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                g2.setColor(dotColor);
                g2.fillOval(0, 10, 12, 12);
            }
        };
        dot.setPreferredSize(new Dimension(20, 30));
        dot.setOpaque(false);

        JPanel texts = new JPanel(new GridLayout(2, 1));
        texts.setOpaque(false);
        JLabel t = new JLabel(title);
        t.setFont(new Font("Segoe UI", Font.BOLD, 14));
        t.setForeground(Color.WHITE);
        JLabel d = new JLabel(desc);
        d.setFont(new Font("Segoe UI", Font.PLAIN, 12));
        d.setForeground(COLOR_MUTED);
        texts.add(t); texts.add(d);

        p.add(dot, BorderLayout.WEST);
        p.add(texts, BorderLayout.CENTER);
        return p;
    }

    class XAIRadarChart extends JPanel {
        private int[] scores = {0, 0, 0, 0, 0};
        private final String[] labels = {"Fake Brand Name", "Panic Words", "Bad Links", "Fake Sender", "Hidden Code"};

        public XAIRadarChart() {
            setOpaque(false);
        }

        public void updateScores(int[] newScores) {
            this.scores = newScores;
            repaint();
        }

        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2 = (Graphics2D) g.create();
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

            int cx = getWidth() / 2 - 50;
            int cy = getHeight() / 2;
            int radius = Math.min(cx, cy) - 40;

            g2.setColor(COLOR_BORDER);
            g2.setStroke(new BasicStroke(1f, BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND, 0, new float[]{4}, 0));
            for (int i = 1; i <= 4; i++) {
                drawWebPolygon(g2, cx, cy, radius * i / 4);
            }

            g2.setStroke(new BasicStroke(1f));
            g2.setFont(new Font("Segoe UI", Font.BOLD, 12));
            for (int i = 0; i < 5; i++) {
                double angle = Math.toRadians(-90 + i * 72);
                int x = (int) (cx + Math.cos(angle) * radius);
                int y = (int) (cy + Math.sin(angle) * radius);
                g2.setColor(COLOR_BORDER);
                g2.drawLine(cx, cy, x, y);

                g2.setColor(COLOR_TEXT);
                int lx = (int) (cx + Math.cos(angle) * (radius + 25));
                int ly = (int) (cy + Math.sin(angle) * (radius + 20));

                if (lx < cx) lx -= g2.getFontMetrics().stringWidth(labels[i]);
                if (i == 0) lx -= g2.getFontMetrics().stringWidth(labels[i]) / 2;

                g2.drawString(labels[i], lx, ly);
            }

            Polygon dataPoly = new Polygon();
            for (int i = 0; i < 5; i++) {
                double angle = Math.toRadians(-90 + i * 72);
                int r = (int) (radius * (scores[i] / 100.0));
                int x = (int) (cx + Math.cos(angle) * r);
                int y = (int) (cy + Math.sin(angle) * r);
                dataPoly.addPoint(x, y);
            }

            g2.setColor(new Color(255, 71, 87, 80));
            g2.fillPolygon(dataPoly);

            g2.setColor(COLOR_DANGER);
            g2.setStroke(new BasicStroke(3f));
            g2.drawPolygon(dataPoly);

            g2.setColor(Color.WHITE);
            for (int i = 0; i < 5; i++) {
                g2.fillOval(dataPoly.xpoints[i] - 4, dataPoly.ypoints[i] - 4, 8, 8);
            }

            g2.dispose();
        }

        private void drawWebPolygon(Graphics2D g2, int cx, int cy, int r) {
            Polygon p = new Polygon();
            for (int i = 0; i < 5; i++) {
                double angle = Math.toRadians(-90 + i * 72);
                p.addPoint((int) (cx + Math.cos(angle) * r), (int) (cy + Math.sin(angle) * r));
            }
            g2.drawPolygon(p);
        }
    }

    // --- UI HELPERS ---
    private JPanel createDashboardCard(String title) {
        JPanel p = new JPanel() {
            @Override
            protected void paintComponent(Graphics g) {
                Graphics2D g2 = (Graphics2D) g.create();
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                g2.setColor(COLOR_CARD);
                g2.fill(new RoundRectangle2D.Float(0, 0, getWidth(), getHeight(), 16, 16));
                g2.setColor(COLOR_ACCENT);
                g2.fill(new RoundRectangle2D.Float(0, 0, getWidth(), 4, 16, 16));
                g2.fillRect(0, 2, getWidth(), 2);
                g2.dispose();
            }
        };
        p.setLayout(new BorderLayout());
        p.setOpaque(false);
        p.setBorder(new EmptyBorder(15, 20, 20, 20));

        JLabel titleLbl = new JLabel(title);
        titleLbl.setFont(new Font("Segoe UI", Font.BOLD, 15));
        titleLbl.setForeground(Color.WHITE);
        titleLbl.setBorder(new EmptyBorder(0, 0, 15, 0));
        p.add(titleLbl, BorderLayout.NORTH);

        return p;
    }

    private JPanel createFeatureBlock(String title, JLabel valueLabel) {
        JPanel p = new JPanel() {
            @Override
            protected void paintComponent(Graphics g) {
                Graphics2D g2 = (Graphics2D) g.create();
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                g2.setColor(new Color(40, 46, 58));
                g2.fill(new RoundRectangle2D.Float(0, 0, getWidth(), getHeight(), 12, 12));
                g2.setColor(COLOR_BORDER);
                g2.draw(new RoundRectangle2D.Float(0, 0, getWidth()-1, getHeight()-1, 12, 12));
                g2.dispose();
            }
        };
        p.setLayout(new BorderLayout());
        p.setOpaque(false);

        JLabel tLbl = new JLabel(title, SwingConstants.CENTER);
        tLbl.setFont(new Font("Segoe UI", Font.BOLD, 12));
        tLbl.setForeground(COLOR_MUTED);
        tLbl.setBorder(new EmptyBorder(12, 0, 5, 0));

        valueLabel.setBorder(new EmptyBorder(0, 0, 12, 0));

        p.add(tLbl, BorderLayout.NORTH);
        p.add(valueLabel, BorderLayout.CENTER);
        return p;
    }

    private JPanel createResultRow(String title, JLabel valueLabel) {
        JPanel p = new JPanel(new BorderLayout());
        p.setBackground(COLOR_CARD);
        p.setBorder(new MatteBorder(0, 0, 1, 0, COLOR_BORDER));

        JLabel tLbl = new JLabel(title);
        tLbl.setFont(new Font("Segoe UI", Font.BOLD, 13));
        tLbl.setForeground(COLOR_MUTED);
        tLbl.setBorder(new EmptyBorder(15, 10, 15, 10));

        valueLabel.setBorder(new EmptyBorder(15, 10, 15, 10));
        p.add(tLbl, BorderLayout.WEST);
        p.add(valueLabel, BorderLayout.EAST);
        return p;
    }

    private JLabel createDynamicValueLabel(String text, Color c) {
        JLabel l = new JLabel(text, SwingConstants.CENTER);
        l.setFont(new Font("Segoe UI", Font.BOLD, 18));
        l.setForeground(c);
        return l;
    }

    private JTable styleZebraTable(JTable table) {
        table.setBackground(COLOR_PANEL_INNER);
        table.setForeground(COLOR_TEXT);
        table.setRowHeight(36);
        table.setFont(new Font("Segoe UI", Font.PLAIN, 14));
        table.setShowGrid(false);
        table.setIntercellSpacing(new Dimension(0, 0));
        table.setFillsViewportHeight(true);

        table.setDefaultRenderer(Object.class, new DefaultTableCellRenderer() {
            @Override
            public Component getTableCellRendererComponent(JTable table, Object value, boolean isSelected, boolean hasFocus, int row, int column) {
                Component c = super.getTableCellRendererComponent(table, value, isSelected, hasFocus, row, column);

                if (!isSelected) {
                    c.setBackground(row % 2 == 0 ? COLOR_CARD : COLOR_PANEL_INNER);
                } else {
                    c.setBackground(COLOR_BORDER);
                }

                if (column == 3 && value != null) {
                    String val = value.toString();
                    if (val.equalsIgnoreCase("Safe")) c.setForeground(COLOR_SAFE);
                    else if (val.equalsIgnoreCase("Suspicious")) c.setForeground(COLOR_SUSPICIOUS);
                    else c.setForeground(COLOR_DANGER);
                    setFont(new Font("Segoe UI", Font.BOLD, 14));
                } else {
                    c.setForeground(COLOR_TEXT);
                    setFont(new Font("Segoe UI", Font.PLAIN, 14));
                }

                setHorizontalAlignment(JLabel.CENTER);
                ((JComponent)c).setBorder(new EmptyBorder(0, 5, 0, 5));
                return c;
            }
        });

        JTableHeader header = table.getTableHeader();
        header.setBackground(COLOR_NAV);
        header.setForeground(COLOR_MUTED);
        header.setFont(new Font("Segoe UI", Font.BOLD, 13));
        header.setBorder(BorderFactory.createMatteBorder(0, 0, 2, 0, COLOR_ACCENT));
        header.setPreferredSize(new Dimension(header.getWidth(), 40));
        return table;
    }

    private JScrollPane styleScrollPane(JScrollPane scroll) {
        scroll.setBorder(BorderFactory.createLineBorder(COLOR_BORDER, 1));
        scroll.getViewport().setBackground(COLOR_PANEL_INNER);
        return scroll;
    }

    private JLabel createSectionLabel(String t) {
        JLabel l = new JLabel(t, SwingConstants.LEFT);
        l.setForeground(COLOR_MUTED);
        l.setFont(new Font("Segoe UI", Font.BOLD, 13));
        l.setBorder(new EmptyBorder(5, 0, 8, 0));
        return l;
    }

    private JTextField createStyledTextField() {
        JTextField tf = new JTextField();
        tf.setBackground(COLOR_PANEL_INNER);
        tf.setForeground(Color.WHITE);
        tf.setCaretColor(COLOR_ACCENT);
        tf.setFont(new Font("Segoe UI", Font.PLAIN, 15));
        tf.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(COLOR_BORDER),
                BorderFactory.createEmptyBorder(12, 15, 12, 15)
        ));
        tf.setMaximumSize(new Dimension(Integer.MAX_VALUE, 45));
        return tf;
    }

    class RoundedButton extends JButton {
        public RoundedButton(String text) {
            super(text);
            setContentAreaFilled(false);
            setFocusPainted(false);
            setBorderPainted(false);
            setCursor(new Cursor(Cursor.HAND_CURSOR));

            addMouseListener(new MouseAdapter() {
                public void mouseEntered(MouseEvent evt) {
                    if (isEnabled()) setBackground(getBackground().brighter());
                }
                public void mouseExited(MouseEvent evt) {
                    if (isEnabled()) {
                        if (getText().contains("Scan Email")) {
                            setBackground(COLOR_ACCENT);
                        } else if (getText().contains("Mark as Safe")) {
                            setBackground(COLOR_SAFE);
                        } else if (getText().contains("Mark as Phishing")) {
                            setBackground(COLOR_DANGER);
                        }
                    }
                }
            });
        }

        @Override
        protected void paintComponent(Graphics g) {
            Graphics2D g2 = (Graphics2D) g.create();
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            g2.setColor(isEnabled() ? getBackground() : new Color(45, 55, 68));
            g2.fill(new RoundRectangle2D.Float(0, 0, getWidth(), getHeight(), 8, 8));
            super.paintComponent(g);
            g2.dispose();
        }
    }

    // ==========================================
    // LOGIC & LINK BLOCKER
    // ==========================================

    private void blockDangerousLinks() {
        String originalText = bodyArea.getText();

        String safeText = originalText.replaceAll("(?i)(https?://\\S+|www\\.\\S+)", "[LINK BLOCKED FOR SAFETY]");

        if (!originalText.equals(safeText)) {
            bodyArea.setText(safeText);
            bodyArea.setForeground(new Color(255, 100, 100));

            UIManager.put("OptionPane.messageForeground", COLOR_DANGER);
            JOptionPane.showMessageDialog(this,
                    "For your safety, the bad links in this email have been blocked and removed.",
                    "Links Blocked!",
                    JOptionPane.WARNING_MESSAGE);
            UIManager.put("OptionPane.messageForeground", COLOR_TEXT);
        }
    }

    private void runLiveScan() {
        String sender = senderField.getText().trim();
        String body = bodyArea.getText().trim();

        if (body.isEmpty()) {
            JOptionPane.showMessageDialog(this, "Please enter email content to scan.");
            return;
        }

        bodyArea.setForeground(Color.WHITE);

        scanButton.setEnabled(false);
        feedbackPanel.setVisible(false);
        riskMeter.setValue(0);
        riskMeter.setString("Scanning...");
        valDecision.setText("ANALYZING...");
        valDecision.setForeground(COLOR_MUTED);

        new Thread(() -> {
            try {
                JsonObject res = ApiService.analyzeEmail(sender, body);

                if (res.has("error") || !res.has("phish_score")) {
                    SwingUtilities.invokeLater(() -> {
                        scanButton.setEnabled(true);
                        valDecision.setText("API ERROR");
                        valDecision.setForeground(COLOR_DANGER);
                        riskMeter.setString("Backend Error");
                    });
                    return;
                }

                double score = res.get("phish_score").getAsDouble();
                String classification = res.get("classification").getAsString();
                double levScore = res.has("lev_score") ? res.get("lev_score").getAsDouble() : 0.0;
                double aiProb = res.has("ai_prob") ? res.get("ai_prob").getAsDouble() : score;
                int keywordsCount = res.has("keyword_count") ? res.get("keyword_count").getAsInt() : 0;
                String authCheck = res.has("auth_check") ? res.get("auth_check").getAsString() : "UNVERIFIED";

                SwingUtilities.invokeLater(() -> {
                    scanButton.setEnabled(true);
                    lastSender = sender;
                    lastClassification = classification;
                    int finalScoreInt = (int) score;
                    riskMeter.setValue(finalScoreInt);

                    boolean isDangerous = finalScoreInt >= 75;
                    boolean isSafe = finalScoreInt < 45;

                    // --- Radar Update ---
                    int vBrand = (levScore > 0.84 && levScore < 1.0) ? 95 : (levScore < 0.5 ? 60 : 10);
                    int vNLP = Math.min(100, keywordsCount * 25);
                    int vURL = body.contains("http") ? (isDangerous ? 85 : 40) : 10;
                    int vAuth = authCheck.equals("UNVERIFIED") ? 75 : 10;
                    int vStruct = (body.contains("<html") || body.contains("href")) ? 65 : 15;

                    if (radarChart != null) {
                        radarChart.updateScores(new int[]{vBrand, vNLP, vURL, vAuth, vStruct});
                    }

                    if (isSafe) {
                        feedbackTxt.setText("Did we miss a threat?");
                        btnReportMistake.setText("Mark as Phishing");
                        btnReportMistake.setBackground(COLOR_DANGER);
                    } else {
                        feedbackTxt.setText("False alarm?");
                        btnReportMistake.setText("Mark as Safe");
                        btnReportMistake.setBackground(COLOR_SAFE);
                    }


                    if (isDangerous) {
                        blockDangerousLinks();
                    }

                    boolean hasLinks = body.contains("http");
                    lblFeatLinks.setText(hasLinks ? "Yes" : "No");
                    lblFeatLinks.setForeground(hasLinks ? COLOR_SUSPICIOUS : COLOR_SAFE);

                    lblFeatDomain.setText(String.valueOf(levScore));
                    lblFeatDomain.setForeground(levScore > 0.8 ? COLOR_SAFE : COLOR_DANGER);

                    lblFeatKeywords.setText(String.valueOf(keywordsCount));
                    lblFeatKeywords.setForeground(keywordsCount > 2 ? COLOR_DANGER : COLOR_SAFE);

                    valLevenshtein.setText(String.valueOf(levScore));
                    valAiScore.setText(aiProb + "%");

                    if (isSafe) {
                        valDecision.setText("SAFE EMAIL");
                        valDecision.setForeground(COLOR_SAFE);
                        riskMeter.setForeground(COLOR_SAFE);
                        riskMeter.setString("Threat Level: " + finalScoreInt + "% - Status: SAFE");
                    } else if (!isDangerous) {
                        valDecision.setText("SUSPICIOUS");
                        valDecision.setForeground(COLOR_SUSPICIOUS);
                        riskMeter.setForeground(COLOR_SUSPICIOUS);
                        riskMeter.setString("Threat Level: " + finalScoreInt + "% - Status: SUSPICIOUS");
                    } else {
                        valDecision.setText("DANGEROUS");
                        valDecision.setForeground(COLOR_DANGER);
                        riskMeter.setForeground(COLOR_DANGER);
                        riskMeter.setString("Threat Level: " + finalScoreInt + "% - Status: THREAT BLOCKED");
                    }
                    feedbackPanel.setVisible(true);

                    if (activeHistoryModel != null) refreshLogs(activeHistoryModel);
                    if (fullHistoryModel != null) refreshLogs(fullHistoryModel);
                });
            } catch (Exception ex) {
                SwingUtilities.invokeLater(() -> {
                    scanButton.setEnabled(true);
                    valDecision.setText("OFFLINE");
                    riskMeter.setString("Connection Error");
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
                    if (history != null) {
                        for (JsonElement element : history) {
                            JsonObject obj = element.getAsJsonObject();
                            model.addRow(new Object[]{
                                    obj.get("scan_date").getAsString(),
                                    obj.get("sender_email").getAsString(),
                                    obj.get("phish_score").getAsString() + "%",
                                    obj.get("classification").getAsString()
                            });
                        }
                    }
                });
            } catch (Exception ignored) {}
        }).start();
    }

    private void sendHumanOverride() {
        String correctLabel = (lastClassification.equalsIgnoreCase("Safe")) ? "Phishing" : "Safe";
        new Thread(() -> {
            try {
                ApiService.sendFeedback(lastSender, correctLabel);
                SwingUtilities.invokeLater(() -> {
                    feedbackPanel.setVisible(false);
                    JOptionPane.showMessageDialog(this, "Fixed!\nThe system will now re-scan the email...");
                    runLiveScan();
                });
            } catch (Exception ex) {
                ex.printStackTrace();
            }
        }).start();
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> new MainWindow().setVisible(true));
    }
}