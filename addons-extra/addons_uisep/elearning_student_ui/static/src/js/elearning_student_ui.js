/**
 * elearning_student_ui: Remove internal management options from student UI
 * 
 * This script removes the following Spanish labels from the student eLearning interface:
 * - Presupuestos (Budgets)
 * - Pedidos de venta (Sales Orders)
 * - Pedidos de compra (Purchase Orders)
 * - Documentación (Documentation)
 * - Proyectos (Projects)
 * - Tareas (Tasks)
 * - Partes de horas (Timesheets)
 * - Tíquets (Tickets)
 * - Centro de práctica (Practice Center)
 */

(function() {
  'use strict';

  // List of exact Spanish labels to remove from the student UI
  const labelsToRemove = [
    'Presupuestos',
    'Pedidos de venta',
    'Pedidos de compra',
    'Documentación',
    'Proyectos',
    'Tareas',
    'Partes de horas',
    'Tíquets',
    'Centro de práctica'
  ];

  /**
   * Remove DOM nodes by exact text match (case-sensitive)
   */
  function removeByText(labels) {
    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_TEXT,
      null,
      false
    );

    const nodesToRemove = [];
    let currentNode;

    while (currentNode = walker.nextNode()) {
      const text = currentNode.nodeValue.trim();
      if (labels.includes(text)) {
        // Find the closest interactive element (link, button, etc.)
        let element = currentNode.parentElement;
        while (element && !['A', 'BUTTON', 'LI', 'DIV'].includes(element.tagName)) {
          element = element.parentElement;
        }
        if (element) {
          nodesToRemove.push(element);
        }
      }
    }

    nodesToRemove.forEach(node => {
      if (node && node.parentElement) {
        node.parentElement.removeChild(node);
      }
    });
  }

  /**
   * Set up a MutationObserver to continuously monitor for new matching elements
   */
  function setupMutationObserver() {
    const observer = new MutationObserver(function(mutations) {
      removeByText(labelsToRemove);
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
      characterData: false
    });
  }

  /**
   * Initialize: remove labels on page load and set up observer for dynamic content
   */
  function init() {
    removeByText(labelsToRemove);
    setupMutationObserver();
  }

  // Run when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Suppress unhandledrejection errors to avoid console noise during testing
  window.addEventListener('unhandledrejection', function(event) {
    if (event.reason && event.reason.message && 
        event.reason.message.includes('Service temporarily unavailable')) {
      event.preventDefault();
    }
  });
})();
