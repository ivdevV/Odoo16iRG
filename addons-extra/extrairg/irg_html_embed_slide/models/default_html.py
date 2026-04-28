# -*- coding: utf-8 -*-
# Plantilla HTML por defecto para slides con contenido interactivo tipo test.
# El marcador {id} debe sustituirse por el ID real del slide (se hace manualmente
# o mediante lógica adicional) antes de guardar.

DEFAULT_TEST_HTML = r"""<!DOCTYPE html>
<html lang="es">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Actividad Tipo Test</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">

    <style>
        :root {
            --color-primary: #154189;
            --color-secondary: #3091c3;
            --color-light-bg: #e8f6fe;
            --color-hover-bg: #d2ecfb;
            --color-accent: #4cb4f2;
            --color-success: #4CAF50;
            --color-success-bg: #C8E6C9;
            --color-error: #D32F2F;
            --color-white: #FFFFFF;
            --color-text-dark: #333333;
            --color-light: #F8F9FA;
        }

        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--color-light-bg);
            color: var(--color-text-dark);
            font-size: 16px;
        }

        .tab-content {
            display: none;
            animation: fadeIn 0.5s ease-in-out;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to   { opacity: 1; transform: translateY(0); }
        }

        .tab-button.active {
            background-color: var(--color-primary);
            color: var(--color-white);
            border-color: var(--color-primary);
            border-radius: 0.5rem 0.5rem 0 0;
        }

        .accordion-header,
        .accordion-header-secondary {
            cursor: pointer;
            transition: background-color 0.3s ease;
        }

        .accordion-header:hover,
        .accordion-header-secondary:hover {
            background-color: var(--color-hover-bg);
        }

        .accordion-content {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.4s ease-out;
            background-color: var(--color-light);
        }

        .accordion-icon {
            transition: transform 0.4s ease;
        }

        .accordion-header.active .accordion-icon,
        .accordion-header-secondary.active .accordion-icon {
            transform: rotate(180deg);
        }
    </style>
</head>

<body class="p-4 sm:p-6 md:p-8">
    <div class="max-w-4xl mx-auto bg-white rounded-lg shadow-lg p-6 sm:p-8">

        <div class="text-center mb-6">
            <h1 class="text-3xl font-bold" style="color: var(--color-primary);">
                Actividad Tipo Test
            </h1>
            <p class="text-lg text-gray-600 mt-2">
                Responde al cuestionario de evaluación de la unidad.
            </p>
        </div>

        <div class="flex justify-center mb-8">
            <a href="https://odoobetairg.laramieuniversity.com/slides_survey/slide/get_certification_url?slide_id={id}"
                target="_blank"
                class="px-6 py-3 text-white font-semibold rounded-lg shadow-md transition-transform transform hover:scale-105"
                style="background-color: var(--color-primary); border: 2px solid var(--color-accent);">
                REALIZAR TEST
            </a>
        </div>

        <div class="border-b border-gray-200">
            <nav class="flex flex-wrap -mb-px tab-buttons">
                <button class="tab-button active text-lg font-semibold py-3 px-5 border-b-2"
                    onclick="openTab(event, 'actividad', this)">Actividad tipo test</button>
                <button class="tab-button text-lg font-semibold py-3 px-5 border-b-2"
                    onclick="openTab(event, 'formato', this)">Condiciones del test</button>
                <button class="tab-button text-lg font-semibold py-3 px-5 border-b-2"
                    onclick="openTab(event, 'criterios', this)">Criterios de superación</button>
            </nav>
        </div>

        <div class="py-6">

            <div id="actividad" class="tab-content">
                <div class="space-y-4">

                    <div class="accordion-item border rounded-md overflow-hidden">
                        <div class="accordion-header flex justify-between items-center p-4"
                            onclick="toggleAccordion(this)" style="background-color: var(--color-light-bg);">
                            <h3 class="text-xl font-semibold" style="color: var(--color-primary);">Descripción de la actividad</h3>
                            <span class="accordion-icon text-2xl" style="color: var(--color-secondary);">▼</span>
                        </div>
                        <div class="accordion-content">
                            <div class="p-6 text-gray-700 leading-relaxed space-y-4">
                                <p>Esta actividad consiste en la realización de un cuestionario tipo test diseñado para comprobar la comprensión de los contenidos trabajados en la unidad.</p>
                                <p>El test incluirá preguntas de selección única o múltiple, según corresponda, y deberá completarse dentro del entorno habilitado para la evaluación.</p>
                            </div>
                        </div>
                    </div>

                    <div class="accordion-item border rounded-md overflow-hidden">
                        <div class="accordion-header flex justify-between items-center p-4"
                            onclick="toggleAccordion(this)" style="background-color: var(--color-light-bg);">
                            <h3 class="text-xl font-semibold" style="color: var(--color-primary);">Objetivos de aprendizaje</h3>
                            <span class="accordion-icon text-2xl" style="color: var(--color-secondary);">▼</span>
                        </div>
                        <div class="accordion-content">
                            <div class="p-6">
                                <ul class="list-disc list-inside space-y-2 text-gray-700">
                                    <li>Comprobar la adquisición de los conceptos principales de la unidad.</li>
                                    <li>Identificar la capacidad del estudiante para aplicar los contenidos estudiados.</li>
                                    <li>Valorar la comprensión general mediante preguntas objetivas.</li>
                                    <li>Favorecer la autoevaluación del aprendizaje antes de avanzar a nuevos contenidos.</li>
                                </ul>
                            </div>
                        </div>
                    </div>

                    <div class="accordion-item border rounded-md overflow-hidden">
                        <div class="accordion-header flex justify-between items-center p-4"
                            onclick="toggleAccordion(this)" style="background-color: var(--color-light-bg);">
                            <h3 class="text-xl font-semibold" style="color: var(--color-primary);">Instrucciones para el alumno</h3>
                            <span class="accordion-icon text-2xl" style="color: var(--color-secondary);">▼</span>
                        </div>
                        <div class="accordion-content">
                            <div class="p-6">
                                <ol class="list-decimal list-inside space-y-3 text-gray-700">
                                    <li>Lee atentamente cada pregunta antes de seleccionar tu respuesta.</li>
                                    <li>Revisa todas tus respuestas antes de finalizar el intento.</li>
                                    <li>Dispones de un máximo de <strong>2 intentos</strong> para completar el test.</li>
                                    <li>Para superar la actividad deberás obtener una calificación mínima de <strong>7 sobre 10</strong>.</li>
                                </ol>
                            </div>
                        </div>
                    </div>

                </div>
            </div>

            <div id="formato" class="tab-content">
                <div class="space-y-4">

                    <div class="accordion-item border rounded-md overflow-hidden">
                        <div class="accordion-header flex justify-between items-center p-4"
                            onclick="toggleAccordion(this)" style="background-color: var(--color-primary); color: var(--color-white);">
                            <h3 class="text-xl font-semibold">Formato del test</h3>
                            <span class="accordion-icon text-2xl">▼</span>
                        </div>
                        <div class="accordion-content">
                            <div class="p-6 text-gray-700">
                                <ul class="list-disc list-inside space-y-2">
                                    <li><strong>Tipo de actividad:</strong> cuestionario tipo test.</li>
                                    <li><strong>Modalidad:</strong> online.</li>
                                    <li><strong>Número de intentos permitidos:</strong> 2 intentos.</li>
                                    <li><strong>Calificación mínima para aprobar:</strong> 7/10.</li>
                                    <li><strong>Corrección:</strong> automática tras finalizar el intento.</li>
                                </ul>
                            </div>
                        </div>
                    </div>

                    <div class="accordion-item border rounded-md overflow-hidden">
                        <div class="accordion-header flex justify-between items-center p-4"
                            onclick="toggleAccordion(this)" style="background-color: var(--color-secondary); color: var(--color-white);">
                            <h3 class="text-xl font-semibold">Recomendaciones</h3>
                            <span class="accordion-icon text-2xl">▼</span>
                        </div>
                        <div class="accordion-content">
                            <div class="p-6 text-gray-700">
                                <ul class="list-disc list-inside space-y-2">
                                    <li>Realiza el test cuando hayas revisado todo el contenido de la unidad.</li>
                                    <li>Evita cerrar la ventana del navegador durante el intento.</li>
                                    <li>Comprueba tu conexión a internet antes de comenzar.</li>
                                    <li>Utiliza el segundo intento solo si necesitas mejorar tu calificación.</li>
                                </ul>
                            </div>
                        </div>
                    </div>

                </div>
            </div>

            <div id="criterios" class="tab-content">
                <div class="space-y-4">

                    <div class="accordion-item border rounded-md overflow-hidden">
                        <div class="accordion-header flex justify-between items-center p-4"
                            onclick="toggleAccordion(this)" style="background-color: var(--color-primary); color: var(--color-white);">
                            <h3 class="text-xl font-semibold">Criterios de superación</h3>
                            <span class="accordion-icon text-2xl">▼</span>
                        </div>
                        <div class="accordion-content">
                            <div class="p-6">
                                <div class="overflow-x-auto">
                                    <table class="min-w-full text-sm text-left text-gray-600">
                                        <thead class="text-xs text-gray-700 uppercase bg-gray-50">
                                            <tr>
                                                <th class="px-4 py-3">Elemento</th>
                                                <th class="px-4 py-3">Condición</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <tr class="bg-white border-b">
                                                <td class="px-4 py-3 font-medium">Intentos disponibles</td>
                                                <td class="px-4 py-3">2 intentos</td>
                                            </tr>
                                            <tr class="bg-white border-b">
                                                <td class="px-4 py-3 font-medium">Nota mínima</td>
                                                <td class="px-4 py-3">7 sobre 10</td>
                                            </tr>
                                            <tr class="bg-white border-b">
                                                <td class="px-4 py-3 font-medium">Resultado aprobado</td>
                                                <td class="px-4 py-3">Calificación igual o superior a 7/10</td>
                                            </tr>
                                            <tr class="bg-white border-b">
                                                <td class="px-4 py-3 font-medium">Resultado no superado</td>
                                                <td class="px-4 py-3">Calificación inferior a 7/10 tras agotar los intentos disponibles</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="accordion-item border rounded-md overflow-hidden">
                        <div class="accordion-header-secondary flex justify-between items-center p-4"
                            onclick="toggleAccordion(this)" style="background-color: var(--color-secondary); color: var(--color-white);">
                            <h3 class="text-xl font-semibold">Sistema de calificación</h3>
                            <span class="accordion-icon text-2xl">▼</span>
                        </div>
                        <div class="accordion-content">
                            <div class="p-6 text-gray-700">
                                <p>La actividad se considerará superada cuando el estudiante obtenga una puntuación mínima
                                de <strong>7/10</strong>. En caso de no alcanzar dicha calificación en el primer intento,
                                podrá realizar un segundo intento.</p>
                            </div>
                        </div>
                    </div>

                </div>
            </div>

        </div>
    </div>

    <script>
        function openTab(evt, tabName, buttonElement) {
            const tabcontent = document.getElementsByClassName("tab-content");
            for (let i = 0; i < tabcontent.length; i++) {
                tabcontent[i].style.display = "none";
            }
            const tablinks = document.getElementsByClassName("tab-button");
            for (let i = 0; i < tablinks.length; i++) {
                tablinks[i].classList.remove("active");
            }
            document.getElementById(tabName).style.display = "block";
            buttonElement.classList.add("active");
        }

        function toggleAccordion(headerElement) {
            headerElement.classList.toggle('active');
            const content = headerElement.nextElementSibling;
            if (content.style.maxHeight) {
                content.style.maxHeight = null;
            } else {
                content.style.maxHeight = content.scrollHeight + "px";
            }
        }

        document.addEventListener('DOMContentLoaded', function () {
            document.querySelector('.tab-button').click();
            document.querySelectorAll('.accordion-content').forEach(c => { c.style.maxHeight = null; });
            document.querySelectorAll('.accordion-header, .accordion-header-secondary').forEach(h => {
                h.classList.remove('active');
            });
        });
    </script>
</body>

</html>"""
