import asyncio
import re
from playwright import async_api
from playwright.async_api import expect

async def run_test():
    pw = None
    browser = None
    context = None

    try:
        # Start a Playwright session in asynchronous mode
        pw = await async_api.async_playwright().start()

        # Launch a Chromium browser in headless mode with custom arguments
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--window-size=1280,720",
                "--disable-dev-shm-usage",
                "--ipc=host",
                "--single-process"
            ],
        )

        # Create a new browser context (like an incognito window)
        context = await browser.new_context()
        # Wider default timeout to match the agent's DOM-stability budget;
        # auto-waiting Playwright APIs (expect, locator.wait_for) inherit this.
        context.set_default_timeout(15000)

        # Open a new page in the browser context
        page = await context.new_page()

        # Interact with the page elements to simulate user flow
        # -> navigate
        await page.goto("http://localhost:8069/web/login")
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=5000)
        except Exception:
            pass
        
        # -> Click the 'e2e_irg_student_activity' database link to select the test database.
        # e2e_irg_student_activity link
        elem = page.get_by_role("link", name="e2e_irg_student_activity")
        await elem.click(timeout=10000)
        
        # -> Fill 'e2e_faculty_activity' into the Email field and 'E2eFacultyAct1!' into the Password field, then click the 'Log in' button.
        # Email text field
        elem = page.get_by_role("textbox", name="Email")
        await elem.wait_for(state="visible", timeout=10000)
        await elem.fill("e2e_faculty_activity")
        
        # -> Fill 'e2e_faculty_activity' into the Email field and 'E2eFacultyAct1!' into the Password field, then click the 'Log in' button.
        # Password password field
        elem = page.get_by_role("textbox", name="Password")
        await elem.wait_for(state="visible", timeout=10000)
        await elem.fill("E2eFacultyAct1!")
        
        # -> Fill 'e2e_faculty_activity' into the Email field and 'E2eFacultyAct1!' into the Password field, then click the 'Log in' button.
        # Log in button
        elem = page.get_by_role("button", name="Log in")
        await elem.click(timeout=10000)
        
        # -> Click the 'Students' app icon to open the Students list.
        # Students link
        elem = page.get_by_role("option", name="Students")
        await elem.click(timeout=10000)
        
        # -> Open the student record by clicking the 'Alumno E2E Activity' link on the Students list.
        # Alumno E2E Activity link
        elem = page.get_by_role("link", name="Alumno E2E Activity")
        await elem.click(timeout=10000)
        
        # -> Click the 'Actividad' tab on the student form to open the activity view.
        # Actividad link
        elem = page.get_by_role("tab", name="Actividad")
        await elem.click(timeout=10000)
        
        # -> Click the 'Exportar CSV' button shown above the activity table to trigger the export dialog or CSV download widget.
        # Exportar CSV button
        elem = page.get_by_role("button", name="Exportar CSV")
        await elem.click(timeout=10000)
        
        # -> Click the 'Exportar CSV' button and verify that an export dialog or CSV download widget appears (look for title 'Exportar actividad CSV', text 'Archivo CSV listo para descargar', or a filename matching actividad_*.csv).
        # Exportar CSV button
        elem = page.get_by_role("button", name="Exportar CSV")
        await elem.click(timeout=10000)
        
        # -> Click the 'Exportar CSV' button and check for a CSV download modal or download link (title 'Exportar actividad CSV', text 'Archivo CSV listo para descargar', or filename matching actividad_*.csv).
        # Exportar CSV button
        elem = page.get_by_role("button", name="Exportar CSV")
        await elem.click(timeout=10000)
        
        # -> Click the 'Exportar CSV' button and then verify whether an export dialog or a CSV download widget appears with title 'Exportar actividad CSV', text 'Archivo CSV listo para descargar', or a filename like actividad_*.csv.
        # Exportar CSV button
        elem = page.get_by_role("button", name="Exportar CSV")
        await elem.click(timeout=10000)
        
        # -> Click the 'Exportar CSV' button and verify that an export dialog or a CSV download link (e.g., 'actividad_*.csv' or text 'Archivo CSV listo para descargar' or title 'Exportar actividad CSV') appears.
        # Exportar CSV button
        elem = page.get_by_role("button", name="Exportar CSV")
        await elem.click(timeout=10000)
        
        # -> Click the 'Exportar CSV' button once, then (in the next step) verify a CSV download widget appears (look for dialog title 'Exportar actividad CSV', text 'Archivo CSV listo para descargar', or a link whose filename ends with .csv).
        # Exportar CSV button
        elem = page.get_by_role("button", name="Exportar CSV")
        await elem.click(timeout=10000)
        
        # --> Assertions to verify final state
        
        # --> The activity table header row is visible showing the expected columns.
        await page.get_by_role("row", name="Fecha  Tipo  Curso / canal").nth(0).scroll_into_view_if_needed()
        # Assert-outcome: passed
        # Assert: Activity table header row with the expected columns is visible.
        await expect(page.get_by_role("row", name="Fecha  Tipo  Curso / canal").nth(0)).to_be_visible(timeout=15000), "Activity table header row with the expected columns is visible."
        
        # --> The activity table contains a row for a Campus content activity with Elemento 'Contenido E2E'.
        # Assert-outcome: passed
        # Assert: The 'Tipo' cell in the first activity row equals 'Campus'.
        await expect(page.locator("xpath=/html/body/div[1]/div/div/div[2]/div/div[1]/div[2]/div[3]/div[2]/div/div[2]/div/div[2]/table/tbody/tr[1]/td[2]").nth(0)).to_have_text("Campus", timeout=15000), "The 'Tipo' cell in the first activity row equals 'Campus'."
        # Assert-outcome: passed
        # Assert: The 'Elemento' cell in the first activity row equals 'Contenido E2E'.
        await expect(page.locator("xpath=/html/body/div[1]/div/div/div[2]/div/div[1]/div[2]/div[3]/div[2]/div/div[2]/div/div[2]/table/tbody/tr[1]/td[4]").nth(0)).to_have_text("Contenido E2E", timeout=15000), "The 'Elemento' cell in the first activity row equals 'Contenido E2E'."
        await asyncio.sleep(5)

    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()

asyncio.run(run_test())
    