"""Web Utilities for CertVerify.
Contains automated browser context via Playwright and Human Help sessions.
"""

import os
import time
import sys
import re
from playwright.sync_api import sync_playwright
from dateutil import parser


def print_style(text, type_effects=False, delay=0.4):
    """
    Customizing print for terminal pace.
    Type_effect determines whether it will print character by charater.
    False prints the entire line, then pause for dramatic effect.
    """
    if type_effects:

        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(0.03)  # Typerwriter-like speed
        print()
    else:
        print(text)
        time.sleep(delay)


def date_correcter(user_input):
    """Corrects date format to MM-DD-YYYY, regardless of user input"""

    clean_input = str(user_input).strip()

    if clean_input == "" or "N/A" in clean_input.upper() or "ERROR" in clean_input.upper():
        return "N/A"

    try:
        date_parsed = parser.parse(clean_input, fuzzy=True)
        return date_parsed.strftime("%m-%d-%Y")

    except Exception:
        cleaned = clean_input.replace(
            "EXPIRATION:", "").replace("REVIEW:", "").strip()

        if len(cleaned) > 20:
            return "N/A"

    return cleaned


def search_registry_for_license(database_type, search_query, license_id, license_location, is_headless):
    """
    Automated browswer, looking up credentials and returns expiration date
    """
    scraped_text = "No Data Found"

    _ = license_id

    user_home = os.path.expanduser("~")
    local_browser_path = os.path.join(
        user_home, "AppData", "Local", "ms-playwright")
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = local_browser_path

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=is_headless, slow_mo=1000)  # Chromium as a default

        page = browser.new_page()  # New tab

        try:

            if database_type == "DAPIP":

                print_style("Going to DAPIP Reistry..."
                            "\n(Database of Accredited Postsecondary Institutions and Programs)\n")

                page.goto("https://ope.ed.gov/dapip/#/home")
                time.sleep(2)

                print_style("Locating Search field.\n", delay=0.05)
                print_style(f"Searching: {search_query}\n",
                            type_effects=True, delay=0.05)
                page.locator("input#searchTerm.hidden-sm").fill(search_query)

                print_style("Submitting search form...\n")
                page.keyboard.press("Enter")

                # Waiting for the table to load
                print_style("Patience.. Patience...\n", delay=0.05)
                page.wait_for_selector(".table-responsive", timeout=10000)
                time.sleep(1)

                if page.locator("text=No results found").is_visible():
                    print_style(
                        f"{search_query} not found on DAPIP..\n", type_effects=True)
                    scraped_text = "Instituition not found"

                else:
                    # Since DAPIP uses a table for the results, program is going
                    # try and find the right link, and read the results from it.
                    try:
                        city_selecter = license_location.split(",")[0].strip()
                        print_style(
                            f"Filtering for institution in {city_selecter}...\n", delay=0.05)

                        matching_link = page.locator(
                            f"table.table-striped tr:has-text('{city_selecter}') a.location-name").first

                        if matching_link.is_visible():
                            print_style(
                                "Found a match!\n", delay=0.05)
                            matching_link.click()
                            time.sleep(3)  # Incase there is something to load

                            page.wait_for_selector(
                                ".tab-content", timeout=8000)
                            time.sleep(1)

                            # Visually Showing view of DAPIP's Programmatic Accreditation tab
                            try:
                                prog_tab = page.locator(
                                    "a", has_text="Programmatic Accreditation").first
                                if prog_tab.is_visible():
                                    print_style(
                                        "Viewing programmatic data tabs...\n", delay=0.05)
                                    prog_tab.click()
                                    # Pause so she can actually read it
                                    time.sleep(1.5)

                            except Exception:
                                pass

                            # Collecting the entire DAPIP page text
                            whole_page_text = page.locator("body").inner_text()
                            print_style("Text spotted!\n")
                            scraped_text = whole_page_text

                        else:
                            scraped_text = whole_page_text

                    except Exception as table_error:
                        print_style(
                            f"Oop- Looks like an error occurred: {table_error}\n")
                        scraped_text = "Table Navigation Fail"

            elif database_type == "International Registry":

                print_style(
                    f"Searching for an international license verification on Google: {search_query}\n", type_effects=True, delay=0.05)
                page.goto(
                    f"https://www.google.com/search?q={search_query}+license+verification+registry")

                # Keep the window open for 5 seconds to view top results
                time.sleep(5)
                scraped_text = "International Search Executed Successfully"

                # Going to leave a WIP
                # Client does not require International Database yet.
                # May return to.

            elif database_type == "CCNE":

                print_style(
                    "Going to CCNE Registry...\n(Commission on Collegiate Nursing Education)\n", delay=0.05)
                page.goto(
                    "https://directory.ccnecommunity.org/reports/accprog.asp")
                time.sleep(2)

                # Makes sure button is set to "Institution"
                try:
                    page.locator("input[value='institution']").check(
                        timeout=3000)
                except Exception:
                    # It's set to institution automatically as default so if an error happens, we move on.
                    pass

                print_style("Parsing location data...\n", delay=0.05)

                # Filtering by State
                try:
                    state_target = license_location.split(",")[1].strip()
                    page.locator("select[name='state']").select_option(
                        label=re.compile(state_target, re.IGNORECASE)
                    )
                    print_style(
                        f"Filtering by state: {state_target}\n", delay=0.05)

                except Exception:
                    # Skips dropdown menu if all else fails
                    print_style("Searching nationwide...\n", delay=0.05)

                time.sleep(1)

                print_style(
                    f"Submitting CCNE search for: {search_query}\n", delay=0.05)
                page.locator("input[type='submit']").click()

                print_style("Patience.. Patience...\n", delay=0.05)
                page.wait_for_selector("body", timeout=10000)
                time.sleep(2)

                # Slurp the entire results table text off the screen!
                whole_page_text = page.locator("body").inner_text()

                # CCNE has left no option for "no results", so we don't need to add anything in case "no results" comes up.

                if len(whole_page_text) > 50000:
                    print_style(
                        "Lots to look through! Narrowing down...\n", delay=0.05)

                    # Find exactly where the school name is located in the giant string
                    search_index = whole_page_text.lower().find(search_query.lower())

                    # Backup just in case the name fails, we search by city.
                    if search_index == -1:
                        try:
                            city_target = license_location.split(",")[
                                0].strip()
                            if len(city_target) > 3:
                                search_index = whole_page_text.lower().find(city_target.lower())

                            if search_index != -1:
                                print_style(
                                    f"School name not found, searching city: {city_target}...\n", delay=0.05)
                        except Exception:
                            pass

                    if search_index != -1:
                        # Collecting 500 characters before the name, and 4000 characters after it!
                        start = max(0, search_index - 500)
                        end = min(len(whole_page_text), search_index + 4000)

                        scraped_text = whole_page_text[start:end]
                        print_style(
                            "Found a snippet to search!\n", delay=0.05)
                    else:
                        print_style(
                            "Could not locate institution in CCNE directory.\n", delay=0.05)
                        scraped_text = "Institution not found"

            else:
                print_style(
                    f"Database {database_type} isn't setup for automation. Skipping...\n", delay=0.05)
                scraped_text = "Unsupported Database"

            return scraped_text

        except Exception as e:
            print(f" Error: Web autmation. {str(e)}\n")
            return "ERROR"

        finally:

            browser.close()


def manual_login_help(database_name, search_query, license_id, license_name, license_location):
    """
    Opens registry, allows user to login, or pauses if user declines to do so.
    User may enter in expiration date manually or skip a row.
    """

    print_style(
        f"Assistance Mode for {database_name} starting....", type_effects=True, delay=0.05)

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page()

        try:
            if database_name == "FSMB":
                page.goto("https://fsmbb2c.b2clogin.com/fsmbb2c.onmicrosoft.com/b2c_1_signuppolicy/oauth2/v2.0/authorize?client_id=9bf420b1-2396-4698-99c6-338b5c501289&redirect_uri=https%3A%2F%2Fraven.fsmb.org%2Fsignin-oidc&response_type=id_token&scope=openid%20profile&response_mode=form_post&nonce=639165958063926498.YTE5YjdlNzEtNWFiNC00MDNiLTg5ZTEtM2IxOTQ5MmNlNzYyYTk2YTM4OWUtMTUxNy00NTE1LTgxZTAtNTM4YWZmMjdhYzg1&client_info=1&x-client-brkrver=IDWeb.4.8.0.0&state=CfDJ8KJDpb_f_J5CtPuO10g0pxSL__mK2DUjEd3c-niVCK8obmg0CyYi560IJsKFXRnvechfUZ_PsFKUrecNfvLQGEP_jBV63ISjASv1EBQgxSwLv1nSSdloHTbGBOBxLJUqCUQgh918wZeEbScPsVY-0jkapwhmr2bZ0C47F506MghRTxxlB6rfbEEv9LhwlOYa8Uaf481kobaSIFQBbM0xnv6oxsOqeEk-IFfOCQTA-HqGBfEP5jAgP-7LGwIxZdl45nyp7oRnw3VltJrzc0qj07Ji6qKG1_lT3IdyA30MWY8kDp9a1OwGUanPpWIiPWoCN3O7hbylhvqKOU2vyRrlnhPeCp2J6i2x_0bwRxUZroTDbGZ0gADX8y_9F6my1dk56484CXg2ZH9HRWi_A0HjgtMH614SCr4J1TVRtHyzexan24mjgbXuSO889bn_d2nB6mT6VAIlpc9Kg8DESaSC2SCAzNkoOWq4kupIap6ydbBGusdfiGSyEt8oYnKKvTm9zTNuN1r-8xtNakKSfpeTVNWW0tUCedhhZIUQnhnk2VZfeePC5czIebEqGTPjiZznCBf4cpA8OSnohERDUeyB_OPFvNUNQQ9boSsGLalTpkdSJcBghgWHf17-30N7L2vBssrqLn3SjyuqqrBzMx5qaB0xG6or0IDQoa7AAS3wNCdvojRmYRZRd63crKkJkhR8tYJndGY31sp2kgpgIYdxGjy21u214nWcGNF8ws6QokknIIbdqgP3TtquKsq_pXJeF2BK1Y9iTCruCx_Pjhuu1JUK42Z56C1U0bVjitu9sYPHJ9iH5d-1YvVuBeYSv2nKDB5TovSecfjYCE936p1DsXe6nv6o3sJOKlwOM9tkiyiGjsf1egrN06Tr8HwpRIjqx7Az0kIA5qNXEpN--eTj1umI0Vf4XJPf85hErg6B6nhkU3iOOgWHpDZWEsQ1Qu081v7bRvq9-R7cw9Iz2BRSrBnkyXPdf-FDYbHnQLdu2Bo7gujryOTAELoZ8CcCr1Drjg&x-client-SKU=ID_NET10_0&x-client-ver=8.16.0.0")

            else:
                print_style(
                    f"Performing Google Search for {database_name.upper()}\n", delay=0.05)
                page.goto(
                    f"https://www.google.com/search?q={database_name}+verification+portal")

            print_style("\n==================================================")
            print_style(
                f"👋 USER ASSIST MODE ACTIVE FOR: {database_name.upper()}", type_effects=True, delay=0.05)
            print_style(
                "===========================================================")
            print_style(
                f" • Client:        {search_query}\n", delay=0.05)
            print_style(
                f" • License Name:    {license_name}\n", delay=0.05)
            print_style(
                f" • Location:    {license_location}\n", delay=0.05)
            print_style(
                f" • License ID:    {license_id}\n\n", delay=0.05)
            print_style(
                "===========================================================")

            print_style(
                "-----------------------------------------------------------")
            print_style(" INSTRUCTIONS:\n")
            print_style(" 1. Log into the portal in the opened window.\n",
                        delay=0.05)
            print_style(" 2. Find the client's record expiration date.\n",
                        delay=0.05)
            print_style(" 3. Type or copy-paste that date below.\n",
                        delay=0.05)
            print_style("    (Or just press ENTER with nothing to skip!)\n",
                        delay=0.05)
            print_style(
                "==============================================================\n")

            time.sleep(1)

            user_date_input = input(
                "Please enter the expiration date ♥ Thank yooou!\n\nOr Press Enter to skip this row\n")

            corrected_date = date_correcter(user_date_input)

            print_style(
                f"Recieved: '{corrected_date}'! \nThank you for your help ♥!\n\n Progress Stored", type_effects=True)

            return corrected_date

        except Exception as e:
            print(f"Help Mode ended unexpectedly: {e}\n")
            return "Help Mode Error"

        finally:
            browser.close()
