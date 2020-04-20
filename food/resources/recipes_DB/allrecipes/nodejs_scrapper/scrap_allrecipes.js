const fs = require('fs');
const puppeteer = require('puppeteer');

function extractItems() {
  const extractedElements = document.querySelectorAll('div.fixed-recipe-card__info > h3 > a');
  const numOfReviews = document.querySelectorAll('span.fixed-recipe-card__reviews');
  const numOfReviewsj = document.querySelectorAll('grid.grid-col__ratings');
  // grid-col__reviews ng-binding --> span
  // grid-col__ratings --> class
  const items = [];
  var i = 0; var j = 0;
  for (let element of extractedElements) {
  	var n = "NA";
  	if (numOfReviews[i]){
  		n = numOfReviews[i].innerText;
  	}
  	else if (numOfReviewsj[j]){ 
  		n = numOfReviewsj[j].innerText;
  		j++;
  	};
  	var id = element.href.split("/recipe/")[1].split("/")[0] + "/" + element.href.split("/recipe/")[1].split("/")[1];
    items.push(element.innerText + " , " + id + " , "+ n);
    i++;
  }
  return items;
}

async function scrapeInfiniteScrollItems(
  page,
  extractItems,
  itemTargetCount,
  scrollDelay = 5000,
) {
  let items = [];
  try {
    let previousHeight;
    while (items.length < itemTargetCount) {
		items = await page.evaluate(extractItems);
		previousHeight = await page.evaluate('document.body.scrollHeight');
		await page.evaluate('window.scrollTo(0, document.body.scrollHeight)');
		await page.waitForFunction(`document.body.scrollHeight > ${previousHeight}`, {"timeout": 3*1000});
		await page.waitFor(scrollDelay);
    }
  } catch(e) { 
  	var error = "error scrapeInfiniteScrollItems\n" + e;
  	// fs.writeFileSync('./error.txt', error);
  	console.log(error);
  	// return;
  }
  // return items;
  fs.writeFileSync('./recipes.txt', items.join('\n') + '\n');
  return items;
}

function extractNumberOfRes(){
	try{
		const extractedElement = document.querySelectorAll('p.search-results__text > span');
		console.log("We're here");
		console.log(extractedElement);
		const item = extractedElement[0].innerText;
		const numRes = item.match( /\d+/g, '')[0];
		return numRes;
	} catch(e) {
		console.log("Error here");
		// return ["error", "extractNumberOfRes"];
	}
}

(async () => {
	// Set up browser and page.
	const browser = await puppeteer.launch({
	headless: true,
	args: ['--no-sandbox', '--disable-setuid-sandbox'],
	});
	const page = await browser.newPage();
	page.setViewport({ width: 1280, height: 926 });

	// Navigate to the demo page.
	url = 'https://www.allrecipes.com/search/results/?wt=lasagna&sort=re'
	await page.goto(url);
	const numberOfRes = await page.evaluate(extractNumberOfRes) - 1;
	const numberOfPages = numberOfRes / 40 + 1;
	console.log("Pages to go through:", numberOfPages);
	// const numberOfRes = 30;
	fs.writeFileSync('./numberOfRes.txt', numberOfRes); 
	var items = await scrapeInfiniteScrollItems(page, extractItems, numberOfRes);		

	var idx_page = 1;

	while(idx_page<numberOfPages){
		// Scroll and extract items from the page.

		try{
			const new_url = url+'&page='+(++idx_page).toString();
			console.log(new_url);
			await page.goto(new_url);
			var items_p = await scrapeInfiniteScrollItems(page, extractItems, numberOfRes);

			for (let elt of items_p){
				if (items.indexOf(elt) == -1){
					items.push(elt);
				}
			}
			fs.writeFileSync('./recipes_all.txt', items.join('\n') + '\n');

			console.log("Explored page", idx_page);

		} catch (e){
			console.log(e);
			console.log(items_p);
			return;
		}

	}




	// Save extracted items to a file.
	// fs.writeFileSync('./recipes.txt', items.join('\n') + '\n');

	// Close the browser.
	await browser.close();
})();