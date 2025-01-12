from fpdf import FPDF
import matplotlib.pyplot as plt
import io
from datetime import datetime

class StockAnalysisReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Stock Cointegration Analysis Report', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_report(data, apple_adf, meta_adf, rank_test, lag_order, vecm_fit, residuals):
    pdf = StockAnalysisReport()
    pdf.add_page()
    
    # Executive Summary
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Executive Summary', 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 10, 
        f'This report analyzes the cointegration relationship between Apple (AAPL) and Meta (META) stocks '
        f'from {data.index[0].strftime("%Y-%m-%d")} to {data.index[-1].strftime("%Y-%m-%d")}. '
        f'The analysis includes stationarity tests, cointegration analysis, and VECM modeling.'
    )
    pdf.ln(5)

    # Stationarity Test Results
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Stationarity Test Results', 0, 1)
    pdf.set_font('Arial', '', 10)
    
    pdf.multi_cell(0, 10,
        f'Apple (AAPL):\n'
        f'ADF p-value: {apple_adf:.4f}\n'
        f'Series is {"stationary" if apple_adf < 0.05 else "non-stationary"}\n\n'
        f'Meta (META):\n'
        f'ADF p-value: {meta_adf:.4f}\n'
        f'Series is {"stationary" if meta_adf < 0.05 else "non-stationary"}'
    )
    pdf.ln(5)

    # Cointegration Results
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Cointegration Analysis', 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 10,
        f'Cointegration Rank: {rank_test.rank}\n'
        f'Optimal Lag Order: {lag_order.aic}'
    )
    pdf.ln(5)

    # VECM Model Results
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'VECM Model Results', 0, 1)
    pdf.set_font('Arial', '', 10)
    
    # Create plots
    plt.figure(figsize=(12, 8))
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Plot original series
    ax1.plot(data.index, data["Apple"], label="Apple")
    ax1.plot(data.index, data["Meta"], label="Meta")
    ax1.set_title("Original Price Series")
    ax1.legend()
    
    # Plot residuals
    residuals.plot(ax=ax2)
    ax2.set_title("VECM Model Residuals")
    
    plt.tight_layout()
    
    # Save plot to memory
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png', dpi=300, bbox_inches='tight')
    img_buf.seek(0)
    
    # Add plots to PDF
    pdf.image(img_buf, x=10, w=190)
    plt.close()

    # Conclusions
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Conclusions and Recommendations', 0, 1)
    pdf.set_font('Arial', '', 10)
    
    # Add interpretation based on results
    cointegrated = rank_test.rank > 0
    pdf.multi_cell(0, 10,
        f'The analysis {"shows" if cointegrated else "does not show"} evidence of cointegration '
        f'between Apple and Meta stocks. '
        f'This suggests that these stocks {"do" if cointegrated else "do not"} share a long-term '
        f'equilibrium relationship.\n\n'
        f'Trading Implications:\n'
        f'- {"Pairs trading strategies might be viable" if cointegrated else "Pairs trading is not recommended"}\n'
        f'- {"Short-term deviations might present trading opportunities" if cointegrated else "Stocks should be traded independently"}\n'
        f'- Consider market conditions and other factors before making trading decisions'
    )

    # Save the report
    filename = f'stock_analysis_report_{datetime.now().strftime("%Y%m%d")}.pdf'
    pdf.output(filename)
    return filename

# Call this function after your analysis
report_file = generate_report(data, apple_adf, meta_adf, rank_test, lag_order, vecm_fit, residuals)
print(f"Report generated: {report_file}") 