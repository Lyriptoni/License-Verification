import time
from playwright.sync_api import sync_playwright
from dateutil import parser


def date_correcter(user_input):
    """Corrects date format to MM-DD-YYYY, regardless of user input"""

    clean_input = str(user_input).strip()

    if clean_input == "":
        return "Unknown / Not Visible"

    try:
        date_parsed = parser.parse(clean_input, fuzzy=True)

        return date_parsed.strftime("%m-%d-%Y")
    except Exception as e:

        print(f"DEBUG: Parsing fallback triggered due to: {e}")

        return clean_input


def search_registry_for_license(database_type, search_query, license_id, license_location, is_headless):
    """
    Automated browswer, looking up credentials and returns expiration date
    """
    scraped_text = "No Data Found"

    _ = license_id

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=is_headless, slow_mo=1000)  # Chromium as a default

        page = browser.new_page()  # New tab

        try:

            if database_type == "DAPIP":

                print("Going to DAPIP"
                      "\n(Database of Accredited Postsecondary Institutions and Programs)")

                page.goto("https://ope.ed.gov/dapip/#/home")
                time.sleep(2)

                print("Locating Search field.\n")
                print(f"Searching: {search_query}\n")
                page.locator("input#searchTerm.hidden-sm").fill(search_query)

                print("Submitting search form...\n")
                page.keyboard.press("Enter")

                # Waiting for the table to load
                print("Patience.. Patience...\n")
                page.wait_for_selector(".table-responsive", timeout=10000)
                time.sleep(1)

                if page.locator("text=No results found").is_visible():
                    print(f"{search_query} not found on DAPIP..\n")
                    scraped_text = "Instituition not found"

                else:
                    # Since DAPIP uses a table for the results, program is going
                    # try and find the right link, and read the results from it.
                    try:
                        city_selecter = license_location.split(",")[0].strip()
                        print(f"Filtering for institution in {city_selecter}")

                        matching_link = page.locator(
                            f"table.table-striped tr: has-text('{city_selecter}') a.location-name").first

                        if matching_link.is_visible():
                            print("Found a match! Going to view it now!")
                            matching_link.click()
                            time.sleep(3)  # Incase there is something to load

                            page.wait_for_selector(
                                ".accredited-date-range", timeout=8000)
                            time.sleep(1)

                            raw_date_string = page.locator(
                                ".accredited-date-range").inner_text()
                            print(f"Date found as: {raw_date_string}")
                            scraped_text = raw_date_string.replace(
                                "Accredited", "").strip()
                        else:
                            scraped_text = "Searched success, couldn't open profile"

                    except Exception as table_error:
                        print(
                            f"Oop- Looks like an error occurred: {table_error}\n")
                        scraped_text = "Table Navigation Fail"

            elif database_type == "International Registry":

                print(
                    f"Going to International Google Assistant for: {search_query}")
                page.goto(
                    f"https://www.google.com/search?q={search_query}+license+verification+registry")

                # Keep the window open for 10 seconds to view top results
                time.sleep(5)
                scraped_text = "International Search Executed Successfully"
            return scraped_text

        except Exception as e:
            print(f" Error: Web autmation. {str(e)}\n")
            return "Error occurred with verification"

        finally:

            browser.close()


def manual_login_help(database_name, search_query, license_id, license_name, license_location):
    """
    Opens registry, allows user to login, or pauses if user declines to do so.
    User may enter in expiration date manually or skip a row.
    """

    print(f"Assistance Mode for {database_name} starting....")

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page()

        try:
            if database_name == "FSMB":
                page.goto("https://fsmbb2c.b2clogin.com/fsmbb2c.onmicrosoft.com/b2c_1_signuppolicy/oauth2/v2.0/authorize?client_id=9bf420b1-2396-4698-99c6-338b5c501289&redirect_uri=https%3A%2F%2Fraven.fsmb.org%2Fsignin-oidc&response_type=id_token&scope=openid%20profile&response_mode=form_post&nonce=639165958063926498.YTE5YjdlNzEtNWFiNC00MDNiLTg5ZTEtM2IxOTQ5MmNlNzYyYTk2YTM4OWUtMTUxNy00NTE1LTgxZTAtNTM4YWZmMjdhYzg1&client_info=1&x-client-brkrver=IDWeb.4.8.0.0&state=CfDJ8KJDpb_f_J5CtPuO10g0pxSL__mK2DUjEd3c-niVCK8obmg0CyYi560IJsKFXRnvechfUZ_PsFKUrecNfvLQGEP_jBV63ISjASv1EBQgxSwLv1nSSdloHTbGBOBxLJUqCUQgh918wZeEbScPsVY-0jkapwhmr2bZ0C47F506MghRTxxlB6rfbEEv9LhwlOYa8Uaf481kobaSIFQBbM0xnv6oxsOqeEk-IFfOCQTA-HqGBfEP5jAgP-7LGwIxZdl45nyp7oRnw3VltJrzc0qj07Ji6qKG1_lT3IdyA30MWY8kDp9a1OwGUanPpWIiPWoCN3O7hbylhvqKOU2vyRrlnhPeCp2J6i2x_0bwRxUZroTDbGZ0gADX8y_9F6my1dk56484CXg2ZH9HRWi_A0HjgtMH614SCr4J1TVRtHyzexan24mjgbXuSO889bn_d2nB6mT6VAIlpc9Kg8DESaSC2SCAzNkoOWq4kupIap6ydbBGusdfiGSyEt8oYnKKvTm9zTNuN1r-8xtNakKSfpeTVNWW0tUCedhhZIUQnhnk2VZfeePC5czIebEqGTPjiZznCBf4cpA8OSnohERDUeyB_OPFvNUNQQ9boSsGLalTpkdSJcBghgWHf17-30N7L2vBssrqLn3SjyuqqrBzMx5qaB0xG6or0IDQoa7AAS3wNCdvojRmYRZRd63crKkJkhR8tYJndGY31sp2kgpgIYdxGjy21u214nWcGNF8ws6QokknIIbdqgP3TtquKsq_pXJeF2BK1Y9iTCruCx_Pjhuu1JUK42Z56C1U0bVjitu9sYPHJ9iH5d-1YvVuBeYSv2nKDB5TovSecfjYCE936p1DsXe6nv6o3sJOKlwOM9tkiyiGjsf1egrN06Tr8HwpRIjqx7Az0kIA5qNXEpN--eTj1umI0Vf4XJPf85hErg6B6nhkU3iOOgWHpDZWEsQ1Qu081v7bRvq9-R7cw9Iz2BRSrBnkyXPdf-FDYbHnQLdu2Bo7gujryOTAELoZ8CcCr1Drjg&x-client-SKU=ID_NET10_0&x-client-ver=8.16.0.0")

            else:
                print(
                    f"Performing Google Search for {database_name.upper()}\n")
                page.goto(
                    f"https://www.google.com/search?q={database_name}+verification+portal")

            print("\n==================================================")
            print(f"👋 USER ASSIST MODE ACTIVE FOR: {database_name.upper()}")
            print("===========================================================")
            print(f" • Client:        {search_query}\n")
            print(f" • License Name:    {license_name}\n")
            print(f" • Location:    {license_location}\n")
            print(f" • License ID:    {license_id}\n\n")
            print("===========================================================")

            print("-----------------------------------------------------------")
            print(" INSTRUCTIONS:\n")
            print(" 1. Log into the portal in the opened window.\n")
            print(" 2. Find the client's record expiration date.\n")
            print(" 3. Type or copy-paste that date below.\n")
            print("    (Or just press ENTER with nothing to skip!)\n")
            print("==============================================================\n")

            user_date_input = input(
                "Please enter the expiration date ♥ Thank yooou!\n\nOr Press Enter to skip this row\n")

            corrected_date = date_correcter(user_date_input)

            print(
                f"Recieved date: '{corrected_date}'! \nThank you for your help ♥!\n\n Progress Stored")

            return corrected_date

        except Exception as e:
            print(f"Help Mode ended unexpectedly: {e}\n")
            return "Help Mode Error"

        finally:
            browser.close()
