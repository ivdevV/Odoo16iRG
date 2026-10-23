'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');

const sourcePath = path.resolve(__dirname, '../src/frontend/download.js');

function loadEnsurePdfName() {
    const source = fs.readFileSync(sourcePath, 'utf8');
    const context = vm.createContext({ console });
    vm.runInContext(source, context, { filename: sourcePath });
    return context.ensurePdfName;
}

const ensurePdfName = loadEnsurePdfName();

test('título con punto intermedio conserva el punto y acaba en .pdf', () => {
    const name = 'ART 05 Ferrer et al. (2021) Conceptualización';
    assert.equal(ensurePdfName(name), name + '.pdf');
});

test('título sin punto recibe .pdf', () => {
    assert.equal(ensurePdfName('INVENTARIO CSBD-DI'), 'INVENTARIO CSBD-DI.pdf');
});

test('título acabado en .pptx añade .pdf sin sustituir la cola', () => {
    assert.equal(
        ensurePdfName('Parte 2-Evaluación -nov2024.pptx'),
        'Parte 2-Evaluación -nov2024.pptx.pdf'
    );
});

test('otras extensiones de ofimática también acaban en .pdf', () => {
    assert.equal(ensurePdfName('apuntes.docx'), 'apuntes.docx.pdf');
    assert.equal(ensurePdfName('diapositivas.ppt'), 'diapositivas.ppt.pdf');
    assert.equal(ensurePdfName('texto.doc'), 'texto.doc.pdf');
    assert.equal(ensurePdfName('tabla.xlsx'), 'tabla.xlsx.pdf');
});

test('título que ya acaba en .PDF se conserva sin duplicar la extensión', () => {
    assert.equal(ensurePdfName('Informe final.PDF'), 'Informe final.PDF');
    assert.equal(ensurePdfName('et al. (2021).pdf'), 'et al. (2021).pdf');
});

test('vacío, espacios o solo caracteres prohibidos usan documento.pdf', () => {
    assert.equal(ensurePdfName(''), 'documento.pdf');
    assert.equal(ensurePdfName('   '), 'documento.pdf');
    assert.equal(ensurePdfName(null), 'documento.pdf');
    assert.equal(ensurePdfName(undefined), 'documento.pdf');
    assert.equal(ensurePdfName('***'), 'documento.pdf');
});

test('caracteres prohibidos en nombres de archivo se sustituyen', () => {
    const result = ensurePdfName('a\\b/c:d*e?f"g<h>i|j');
    assert.equal(result, 'a b c d e f g h i j.pdf');
    assert.equal(/[\\/:*?"<>|]/.test(result), false);
});

test('Act. en clase y 13.Fluencia no pierden el punto intermedio', () => {
    assert.equal(ensurePdfName('Mini-SEA (Act. en clase)'), 'Mini-SEA (Act. en clase).pdf');
    assert.equal(ensurePdfName('13.Fluencia'), '13.Fluencia.pdf');
});

test('los dos puntos de descarga usan ensurePdfName', () => {
    const source = fs.readFileSync(sourcePath, 'utf8');
    assert.match(source, /downloadPDF\(url\.href,\s*ensurePdfName\(name\)\)/);
    assert.match(source, /filename:\s*ensurePdfName\(name\)/);
});
