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

    // Ultra-Premium Cyber SOC Palette
    private final Color COLOR_BG = new Color(13, 15, 19);
    private final Color COLOR_NAV = new Color(20, 23, 29);
    private final Color COLOR_CARD = new Color(26, 30, 38);
    private final Color COLOR_PANEL_INNER = new Color(34, 39, 49);
    private final Color COLOR_BORDER = new Color(50, 58, 70);
    private final Color COLOR_ACCENT = new Color(0, 168, 255); // Vibrant tech blue
    private final Color COLOR_TEXT = new Color(230, 235, 240);
    private final Color COLOR_MUTED = new Color(140, 150, 160);

    private final Color COLOR_SAFE = new Color(46, 213, 115);
    private final Color COLOR_SUSPICIOUS = new Color(255, 165, 2);
    private final Color COLOR_DANGER = new Color(255, 71, 87);

    private JTextField senderField;
    private JTextArea bodyArea;
    private RoundedButton scanButton;
    private JProgressBar riskMeter;

    // Feature UI
    private JLabel lblFeatLinks;
    private JLabel lblFeatDomain;
    private JLabel lblFeatKeywords;

    // Results UI
    private JLabel valLevenshtein;
    private JLabel valAiScore;
    private JLabel valDecision; // Hero Label

    private JPanel feedbackPanel;
    private JButton btnReportMistake;
    private String lastSender = "";
    private String lastClassification = "";

    private JPanel cardPanel;
    private CardLayout cardLayout;

    private DefaultTableModel activeHistoryModel;

    public MainWindow() {
        setupWindow();
        initUI();
    }

    private void setupWindow() {
        setTitle("PhishAlert - Enterprise Security Dashboard");
        setSize(1400, 880);
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

        JLabel title = new JLabel("PhishAlert Security Dashboard");
        title.setFont(new Font("Segoe UI", Font.BOLD, 26));
        title.setForeground(Color.WHITE);

        JLabel subtitle = new JLabel("Advanced Phishing Detection System");
        subtitle.setForeground(COLOR_ACCENT);
        subtitle.setFont(new Font("Segoe UI", Font.BOLD, 14));

        header.add(title);
        header.add(subtitle);
        topContainer.add(header, BorderLayout.NORTH);

        // --- NAVIGATION ---
        JPanel navBar = new JPanel(new FlowLayout(FlowLayout.LEFT, 10, 0));
        navBar.setBackground(COLOR_NAV);
        navBar.setBorder(new MatteBorder(0, 0, 1, 0, COLOR_BORDER));

        JButton btnTab1 = createNavButton("Scanner");
        JButton btnTab2 = createNavButton("Model Statistics");
        JButton btnTab3 = createNavButton("Scan Database");

        navBar.add(Box.createHorizontalStrut(25));
        navBar.add(btnTab1);
        navBar.add(btnTab2);
        navBar.add(btnTab3);

        topContainer.add(navBar, BorderLayout.SOUTH);
        add(topContainer, BorderLayout.NORTH);

        // --- WORKSPACE ---
        cardLayout = new CardLayout();
        cardPanel = new JPanel(cardLayout);
        cardPanel.setBackground(COLOR_BG);
        cardPanel.setBorder(new EmptyBorder(20, 20, 20, 20));

        cardPanel.add(createScannerTab(), "Scanner");
        cardPanel.add(createStatisticsTab(), "Model Statistics");
        cardPanel.add(createDatabaseTab(), "Scan Database");

        add(cardPanel, BorderLayout.CENTER);

        btnTab1.addActionListener(e -> { cardLayout.show(cardPanel, "Scanner"); updateNavState(btnTab1, btnTab2, btnTab3); });
        btnTab2.addActionListener(e -> { cardLayout.show(cardPanel, "Model Statistics"); updateNavState(btnTab2, btnTab1, btnTab3); });
        btnTab3.addActionListener(e -> { cardLayout.show(cardPanel, "Scan Database"); updateNavState(btnTab3, btnTab1, btnTab2); });

        updateNavState(btnTab1, btnTab2, btnTab3);

        // --- FOOTER ---
        JPanel footer = new JPanel();
        footer.setLayout(new BoxLayout(footer, BoxLayout.Y_AXIS));
        footer.setBackground(COLOR_BG);
        footer.setBorder(new EmptyBorder(10, 35, 20, 35));

        riskMeter = new JProgressBar(0, 100);
        riskMeter.setValue(0);
        riskMeter.setStringPainted(true);
        riskMeter.setFont(new Font("Segoe UI", Font.BOLD, 14));
        riskMeter.setString("System Standby - Ready for payload ingestion");
        riskMeter.setForeground(Color.GRAY);
        riskMeter.setBackground(COLOR_CARD);
        riskMeter.setBorder(BorderFactory.createLineBorder(COLOR_BORDER, 1));
        riskMeter.setMaximumSize(new Dimension(1400, 35));
        riskMeter.setAlignmentX(Component.CENTER_ALIGNMENT);

        feedbackPanel = new JPanel(new FlowLayout(FlowLayout.CENTER, 15, 0));
        feedbackPanel.setBackground(COLOR_BG);
        feedbackPanel.setVisible(false);

        JLabel feedbackTxt = new JLabel("Did the system misclassify this email?");
        feedbackTxt.setForeground(COLOR_MUTED);
        feedbackTxt.setFont(new Font("Segoe UI", Font.PLAIN, 13));

        btnReportMistake = new RoundedButton("Report Mistake & Update Weights");
        btnReportMistake.setBackground(COLOR_DANGER);
        btnReportMistake.setForeground(Color.WHITE);
        btnReportMistake.setFont(new Font("Segoe UI", Font.BOLD, 12));
        btnReportMistake.setPreferredSize(new Dimension(240, 35));
        btnReportMistake.setCursor(new Cursor(Cursor.HAND_CURSOR));

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

        // Hover Effect
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

    private void updateNavState(JButton active, JButton inactive1, JButton inactive2) {
        active.setForeground(COLOR_ACCENT);
        active.setBackground(COLOR_BG); // Blend with background
        active.setBorder(new MatteBorder(3, 1, 0, 1, COLOR_BORDER)); // Top pop

        inactive1.setForeground(COLOR_MUTED);
        inactive1.setBackground(COLOR_NAV);
        inactive1.setBorder(new EmptyBorder(12, 20, 12, 20));

        inactive2.setForeground(COLOR_MUTED);
        inactive2.setBackground(COLOR_NAV);
        inactive2.setBorder(new EmptyBorder(12, 20, 12, 20));
    }

    // ==========================================
    // TAB 1: SCANNER
    // ==========================================
    private JPanel createScannerTab() {
        JPanel panel = new JPanel(new GridLayout(1, 2, 25, 0));
        panel.setBackground(COLOR_BG);

        // LEFT SIDE (Inputs)
        JPanel leftCard = createDashboardCard("Analysis Input Vector");
        leftCard.setLayout(new BoxLayout(leftCard, BoxLayout.Y_AXIS));

        leftCard.add(createSectionLabel("Sender Email Address:"));
        senderField = createStyledTextField();
        leftCard.add(senderField);
        leftCard.add(Box.createVerticalStrut(20));

        leftCard.add(createSectionLabel("Email Payload (Body Content):"));
        bodyArea = new JTextArea();
        bodyArea.setBackground(COLOR_PANEL_INNER);
        bodyArea.setForeground(Color.WHITE);
        bodyArea.setFont(new Font("Segoe UI", Font.PLAIN, 15));
        bodyArea.setCaretColor(COLOR_ACCENT);
        bodyArea.setLineWrap(true);
        bodyArea.setWrapStyleWord(true);
        bodyArea.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        JScrollPane scroll = styleScrollPane(new JScrollPane(bodyArea));
        scroll.setPreferredSize(new Dimension(Integer.MAX_VALUE, 300)); // Gave body area more explicit height
        leftCard.add(scroll);
        leftCard.add(Box.createVerticalStrut(20));

        leftCard.add(createSectionLabel("Extracted Structural Features:"));
        JPanel featureGrid = new JPanel(new GridLayout(1, 3, 10, 10)); // Changed to 1 row, 3 columns
        featureGrid.setBackground(COLOR_CARD);

        lblFeatLinks = createDynamicValueLabel("-", COLOR_TEXT);
        lblFeatDomain = createDynamicValueLabel("-", COLOR_TEXT);
        lblFeatKeywords = createDynamicValueLabel("-", COLOR_TEXT);

        featureGrid.add(createFeatureBlock("Contains Links", lblFeatLinks));
        featureGrid.add(createFeatureBlock("Domain Distance", lblFeatDomain));
        featureGrid.add(createFeatureBlock("Keywords Count", lblFeatKeywords));

        featureGrid.setMaximumSize(new Dimension(Integer.MAX_VALUE, 80)); // Reduced height to allow more space for the body
        leftCard.add(featureGrid);
        leftCard.add(Box.createVerticalStrut(25));

        scanButton = new RoundedButton("Scan Email");
        scanButton.setBackground(COLOR_ACCENT); // Made button blue
        scanButton.setPreferredSize(new Dimension(Integer.MAX_VALUE, 50));
        scanButton.setFont(new Font("Segoe UI", Font.BOLD, 16));
        leftCard.add(scanButton);

        panel.add(leftCard);

        // RIGHT SIDE (Outputs)
        JPanel rightWrapper = new JPanel(new GridLayout(2, 1, 0, 20));
        rightWrapper.setBackground(COLOR_BG);

        JPanel telemetryCard = createDashboardCard("Telemetry Results");
        telemetryCard.setLayout(new BorderLayout());

        // Hero Verdict Label
        JPanel heroPanel = new JPanel(new BorderLayout());
        heroPanel.setBackground(COLOR_CARD);
        heroPanel.setBorder(new MatteBorder(0, 0, 1, 0, COLOR_BORDER));

        JLabel heroTitle = new JLabel("System Verdict", SwingConstants.CENTER);
        heroTitle.setForeground(COLOR_MUTED);
        heroTitle.setFont(new Font("Segoe UI", Font.BOLD, 14));
        heroTitle.setBorder(new EmptyBorder(10, 0, 5, 0));

        valDecision = new JLabel("WAITING", SwingConstants.CENTER);
        valDecision.setFont(new Font("Segoe UI", Font.BOLD, 28));
        valDecision.setForeground(COLOR_MUTED);
        valDecision.setBorder(new EmptyBorder(0, 0, 15, 0));

        heroPanel.add(heroTitle, BorderLayout.NORTH);
        heroPanel.add(valDecision, BorderLayout.CENTER);
        telemetryCard.add(heroPanel, BorderLayout.NORTH);

        // Detailed rows (Removed Auth Row)
        JPanel detailsPanel = new JPanel(new GridLayout(2, 1, 0, 0));
        detailsPanel.setBackground(COLOR_CARD);
        valLevenshtein = createDynamicValueLabel("-", COLOR_ACCENT);
        valAiScore = createDynamicValueLabel("-", COLOR_ACCENT);

        detailsPanel.add(createResultRow("Domain Similarity Score", valLevenshtein));
        detailsPanel.add(createResultRow("Machine Learning Probability", valAiScore));
        telemetryCard.add(detailsPanel, BorderLayout.CENTER);

        rightWrapper.add(telemetryCard);

        JPanel shortHistoryCard = createDashboardCard("Recent Network Traffic");
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
        JPanel panel = new JPanel(new GridLayout(2, 1, 0, 20));
        panel.setBackground(COLOR_BG);

        JPanel rfCard = createDashboardCard("Random Forest Configuration (Ensemble Weight: 70%)");
        rfCard.setLayout(new BorderLayout(15, 15));

        JPanel rfContent = new JPanel(new GridLayout(1, 2, 20, 0));
        rfContent.setBackground(COLOR_CARD);

        JPanel rfMetrics = new JPanel(new GridLayout(3, 1, 0, 15));
        rfMetrics.setBackground(COLOR_CARD);
        rfMetrics.add(createVisualMetricBlock("Accuracy Rating", 57.72, COLOR_SAFE));
        rfMetrics.add(createVisualMetricBlock("Recall (Threat Sensitivity)", 30.46, COLOR_SUSPICIOUS));
        rfMetrics.add(createVisualMetricBlock("F1 Harmonic Score", 43.00, COLOR_ACCENT));

        rfContent.add(rfMetrics);
        rfContent.add(createBeautifulConfusionMatrix(13217, 1803, 11692, 5121));
        rfCard.add(rfContent, BorderLayout.CENTER);

        JPanel lrCard = createDashboardCard("Logistic Regression Configuration (Ensemble Weight: 30%)");
        lrCard.setLayout(new BorderLayout(15, 15));

        JPanel lrContent = new JPanel(new GridLayout(1, 2, 20, 0));
        lrContent.setBackground(COLOR_CARD);

        JPanel lrMetrics = new JPanel(new GridLayout(3, 1, 0, 15));
        lrMetrics.setBackground(COLOR_CARD);
        lrMetrics.add(createVisualMetricBlock("Accuracy Rating", 56.07, COLOR_SAFE));
        lrMetrics.add(createVisualMetricBlock("Recall (Threat Sensitivity)", 94.95, COLOR_SAFE));
        lrMetrics.add(createVisualMetricBlock("F1 Harmonic Score", 70.00, COLOR_ACCENT));

        lrContent.add(lrMetrics);
        lrContent.add(createBeautifulConfusionMatrix(1952, 13068, 841, 15972));
        lrCard.add(lrContent, BorderLayout.CENTER);

        panel.add(rfCard);
        panel.add(lrCard);
        return panel;
    }

    // ==========================================
    // TAB 3: DATABASE
    // ==========================================
    private JPanel createDatabaseTab() {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBackground(COLOR_BG);

        JPanel mainLedgerCard = createDashboardCard("Global Ledger Archive");
        mainLedgerCard.setLayout(new BorderLayout());

        String[] cols = {"Scan Timestamp", "Ingested Sender", "Threat Score", "Final Verdict"};
        DefaultTableModel fullModel = new DefaultTableModel(cols, 0);
        JTable fullTable = styleZebraTable(new JTable(fullModel));
        JScrollPane scroll = styleScrollPane(new JScrollPane(fullTable));

        mainLedgerCard.add(scroll, BorderLayout.CENTER);
        panel.add(mainLedgerCard, BorderLayout.CENTER);

        refreshLogs(fullModel);
        return panel;
    }

    // --- UI DESIGN HELPERS ---

    private JPanel createDashboardCard(String title) {
        JPanel p = new JPanel() {
            @Override
            protected void paintComponent(Graphics g) {
                Graphics2D g2 = (Graphics2D) g.create();
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                g2.setColor(COLOR_CARD);
                g2.fill(new RoundRectangle2D.Float(0, 0, getWidth(), getHeight(), 16, 16));

                // Top Accent Line
                g2.setColor(COLOR_ACCENT);
                g2.fill(new RoundRectangle2D.Float(0, 0, getWidth(), 4, 16, 16));
                g2.fillRect(0, 2, getWidth(), 2); // flatten bottom of the line
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
        JPanel p = new JPanel(new BorderLayout());
        p.setBackground(COLOR_PANEL_INNER);
        p.setBorder(BorderFactory.createLineBorder(COLOR_BORDER, 1));

        JLabel tLbl = new JLabel(title, SwingConstants.CENTER);
        tLbl.setFont(new Font("Segoe UI", Font.BOLD, 12));
        tLbl.setForeground(COLOR_MUTED);
        tLbl.setBorder(new EmptyBorder(10, 0, 5, 0));

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
        l.setFont(new Font("Segoe UI", Font.BOLD, 16));
        l.setForeground(c);
        return l;
    }

    // Zebra Striped & Color Coded Table Renderer
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

                // Zebra stripes
                if (!isSelected) {
                    c.setBackground(row % 2 == 0 ? COLOR_CARD : COLOR_PANEL_INNER);
                } else {
                    c.setBackground(COLOR_BORDER);
                }

                // Color code the verdict column (assumes column 3 is Verdict)
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

    private JPanel createVisualMetricBlock(String title, double value, Color barColor) {
        JPanel p = new JPanel(new BorderLayout());
        p.setBackground(COLOR_PANEL_INNER);
        p.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(COLOR_BORDER, 1),
                BorderFactory.createEmptyBorder(12, 15, 12, 15)
        ));

        JLabel tLbl = new JLabel(title, SwingConstants.LEFT);
        tLbl.setFont(new Font("Segoe UI", Font.BOLD, 13));
        tLbl.setForeground(COLOR_MUTED);

        JLabel vLbl = new JLabel(value + "%", SwingConstants.RIGHT);
        vLbl.setFont(new Font("Segoe UI", Font.BOLD, 20));
        vLbl.setForeground(Color.WHITE);

        JPanel topHalf = new JPanel(new BorderLayout());
        topHalf.setBackground(COLOR_PANEL_INNER);
        topHalf.add(tLbl, BorderLayout.WEST);
        topHalf.add(vLbl, BorderLayout.EAST);
        topHalf.setBorder(new EmptyBorder(0,0,8,0));

        JProgressBar gauge = new JProgressBar(0, 100);
        gauge.setValue((int)value);
        gauge.setPreferredSize(new Dimension(100, 6));
        gauge.setForeground(barColor);
        gauge.setBackground(COLOR_CARD);
        gauge.setBorderPainted(false);

        p.add(topHalf, BorderLayout.CENTER);
        p.add(gauge, BorderLayout.SOUTH);
        return p;
    }

    private JPanel createBeautifulConfusionMatrix(int tn, int fp, int fn, int tp) {
        JPanel container = new JPanel(new BorderLayout());
        container.setBackground(COLOR_CARD);

        JPanel grid = new JPanel(new GridLayout(3, 3, 5, 5));
        grid.setBackground(COLOR_CARD);

        grid.add(new JLabel(""));
        grid.add(createStyledMatrixHeader("Predicted SAFE"));
        grid.add(createStyledMatrixHeader("Predicted THREAT"));

        grid.add(createStyledMatrixHeader("Actual SAFE"));
        grid.add(createMatrixCell(String.valueOf(tn), "True Negative", new Color(39, 174, 96, 40), COLOR_SAFE));
        grid.add(createMatrixCell(String.valueOf(fp), "False Positive", new Color(243, 156, 18, 40), COLOR_SUSPICIOUS));

        grid.add(createStyledMatrixHeader("Actual THREAT"));
        grid.add(createMatrixCell(String.valueOf(fn), "False Negative", new Color(211, 84, 0, 40), COLOR_DANGER));
        grid.add(createMatrixCell(String.valueOf(tp), "True Positive", new Color(39, 174, 96, 40), COLOR_SAFE));

        container.add(grid, BorderLayout.CENTER);
        return container;
    }

    private JLabel createStyledMatrixHeader(String text) {
        JLabel l = new JLabel(text, SwingConstants.CENTER);
        l.setFont(new Font("Segoe UI", Font.BOLD, 12));
        l.setForeground(COLOR_MUTED);
        l.setOpaque(true);
        l.setBackground(COLOR_PANEL_INNER);
        l.setBorder(BorderFactory.createLineBorder(COLOR_BORDER, 1));
        return l;
    }

    private JPanel createMatrixCell(String bigNum, String smallText, Color bgColor, Color textColor) {
        JPanel p = new JPanel(new BorderLayout());
        p.setBackground(bgColor);
        p.setBorder(BorderFactory.createLineBorder(textColor.darker(), 1));

        JLabel lMain = new JLabel(bigNum, SwingConstants.CENTER);
        lMain.setFont(new Font("Segoe UI", Font.BOLD, 24));
        lMain.setForeground(Color.WHITE);
        lMain.setBorder(new EmptyBorder(15, 0, 0, 0));

        JLabel lSub = new JLabel(smallText, SwingConstants.CENTER);
        lSub.setFont(new Font("Segoe UI", Font.BOLD, 11));
        lSub.setForeground(textColor);
        lSub.setBorder(new EmptyBorder(0, 0, 15, 0));

        p.add(lMain, BorderLayout.CENTER);
        p.add(lSub, BorderLayout.SOUTH);
        return p;
    }

    private JLabel createSectionLabel(String t) {
        JLabel l = new JLabel(t);
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
                    setBackground(getBackground().brighter());
                }
                public void mouseExited(MouseEvent evt) {
                    setBackground(getBackground().darker());
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
    // LOGIC
    // ==========================================
    private void runLiveScan() {
        String sender = senderField.getText().trim();
        String body = bodyArea.getText().trim();

        if (body.isEmpty()) {
            JOptionPane.showMessageDialog(this, "Please enter email content to scan.");
            return;
        }

        scanButton.setEnabled(false);
        feedbackPanel.setVisible(false);
        riskMeter.setValue(0);
        riskMeter.setString("Scanning Payload...");
        valDecision.setText("ANALYZING...");
        valDecision.setForeground(COLOR_MUTED);

        new Thread(() -> {
            try {
                JsonObject res = ApiService.analyzeEmail(sender, body);
                double score = res.get("phish_score").getAsDouble();
                String classification = res.get("classification").getAsString();
                double levScore = res.has("lev_score") ? res.get("lev_score").getAsDouble() : 0.0;
                double aiProb = res.has("ai_prob") ? res.get("ai_prob").getAsDouble() : score;
                int keywordsCount = res.has("keyword_count") ? res.get("keyword_count").getAsInt() : 0;

                SwingUtilities.invokeLater(() -> {
                    scanButton.setEnabled(true);
                    lastSender = sender;
                    lastClassification = classification;
                    int finalScoreInt = (int) score;
                    riskMeter.setValue(finalScoreInt);

                    boolean isDangerous = finalScoreInt >= 75;
                    boolean isSafe = finalScoreInt < 45;

                    if (isDangerous) {
                        String originalText = bodyArea.getText();
                        String sanitizedText = originalText.replaceAll("(?i)\\b(https?://|www\\.)\\S+\\b", "[MALICIOUS_LINK_BLOCKED]");
                        if (!originalText.equals(sanitizedText)) {
                            bodyArea.setText(sanitizedText);
                        }

                        UIManager.put("OptionPane.messageForeground", COLOR_DANGER);
                        JOptionPane.showMessageDialog(this,
                                "SECURITY ALERT: Malicious Payload Detected (Score: " + finalScoreInt + "%).\nStructural links have been disabled to protect the host.",
                                "Threat Neutralized",
                                JOptionPane.WARNING_MESSAGE);
                        UIManager.put("OptionPane.messageForeground", COLOR_TEXT);
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

                    if (activeHistoryModel != null) {
                        refreshLogs(activeHistoryModel);
                    }
                });
            } catch (Exception ex) {
                SwingUtilities.invokeLater(() -> {
                    scanButton.setEnabled(true);
                    valDecision.setText("OFFLINE");
                    riskMeter.setString("Connection Error - Engine Offline");
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
                    if (history != null && history.size() > 0) {
                        for (JsonElement element : history) {
                            JsonObject obj = element.getAsJsonObject();
                            model.addRow(new Object[]{
                                    obj.get("scan_date").getAsString(),
                                    obj.get("sender_email").getAsString(),
                                    obj.get("phish_score").getAsString() + "%",
                                    obj.get("classification").getAsString()
                            });
                        }
                    } else {
                        injectDemoData(model);
                    }
                });
            } catch (Exception ex) {
                SwingUtilities.invokeLater(() -> {
                    if(model.getRowCount() == 0) {
                        injectDemoData(model);
                    }
                });
            }
        }).start();
    }

    private void injectDemoData(DefaultTableModel model) {
        model.addRow(new Object[]{"2026-06-01 15:30:12", "accounts-update@g00gle.com", "79.50%", "Dangerous"});
        model.addRow(new Object[]{"2026-06-01 14:22:05", "newsletter@medium.com", "12.10%", "Safe"});
        model.addRow(new Object[]{"2026-06-01 11:05:44", "security@paypa1.com", "85.00%", "Dangerous"});
    }

    private void sendHumanOverride() {
        String correctLabel = (!lastClassification.equalsIgnoreCase("Dangerous")) ? "Phishing" : "Safe";

        new Thread(() -> {
            try {
                ApiService.sendFeedback(lastSender, correctLabel);
                SwingUtilities.invokeLater(() -> {
                    feedbackPanel.setVisible(false);
                    JOptionPane.showMessageDialog(this, "Feedback Processed!\nThe system is adjusting weights and rescanning the email...");
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