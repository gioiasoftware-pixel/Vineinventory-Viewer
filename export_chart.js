const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

async function exportChart() {
    console.log('🚀 Avvio esportazione grafico...');
    
    const htmlPath = path.join(__dirname, 'chart_preview.html');
    const outputPath = path.join(__dirname, 'grafico-flusso-movimenti.jpg');
    
    // Verifica che il file HTML esista
    if (!fs.existsSync(htmlPath)) {
        console.error('❌ File chart_preview.html non trovato!');
        process.exit(1);
    }
    
    const browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    try {
        const page = await browser.newPage();
        
        // Imposta la dimensione della viewport per un grafico grande
        await page.setViewport({
            width: 1400,
            height: 1000
        });
        
        // Carica il file HTML
        const fileUrl = `file://${htmlPath}`;
        console.log(`📄 Caricamento: ${fileUrl}`);
        await page.goto(fileUrl, {
            waitUntil: 'networkidle0',
            timeout: 30000
        });
        
        // Aspetta che Chart.js renderizzi il grafico
        console.log('⏳ Attesa renderizzazione grafico...');
        await page.waitForFunction(
            'typeof Chart !== "undefined" && document.getElementById("movements-chart")',
            { timeout: 10000 }
        );
        
        // Aspetta un po' per assicurarsi che il grafico sia completamente renderizzato
        await page.waitForTimeout(2000);
        
        // Trova il canvas del grafico
        const canvas = await page.$('#movements-chart');
        
        if (!canvas) {
            throw new Error('Canvas del grafico non trovato!');
        }
        
        // Fai lo screenshot del canvas
        console.log('📸 Cattura screenshot...');
        await canvas.screenshot({
            path: outputPath,
            type: 'jpeg',
            quality: 95
        });
        
        console.log(`✅ Grafico esportato con successo: ${outputPath}`);
        
    } catch (error) {
        console.error('❌ Errore durante l\'esportazione:', error);
        process.exit(1);
    } finally {
        await browser.close();
    }
}

// Esegui l'esportazione
exportChart();
