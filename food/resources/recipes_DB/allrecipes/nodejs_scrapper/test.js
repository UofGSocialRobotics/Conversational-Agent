const fs = require('fs');
const puppeteer = require('puppeteer');

function extractItems() {
  const extractedElements = document.querySelectorAll('li.cook-info > h4');
  const items = [];
  for (let element of extractedElements) {
  	items.push(element.innerText);
  }
  return items;
}


// ---------------------------------------------------------------------- //
//								MAIN FUNCTION				    		  //
// ---------------------------------------------------------------------- //

(async () => {

	// Set up browser and page.
	const browser = await puppeteer.launch({
	headless: true,
	args: ['--no-sandbox', '--disable-setuid-sandbox'],
	});
	const page = await browser.newPage();
	page.setViewport({ width: 1280, height: 926 });

	// Navigate to the demo page.
	// url = 'https://www.allrecipes.com/recipe/255462/lasagna-flatbread'
	const url = 'https://www.allrecipes.com/recipe/255462/lasagna-flatbread/'
	await page.goto(url);

	// click does not work
	// await page.$eval('div.recipe-reviews__more-container > div.more-button', e => e.click());
	await page.click('div.recipe-reviews__more-container > div.more-button');
	// console.log(moreBtn);
	const items = await page.evaluate(extractItems);

	try{
		console.log(items);
	} catch(e) {
		console.log(e);
	}

	await browser.close();

})();