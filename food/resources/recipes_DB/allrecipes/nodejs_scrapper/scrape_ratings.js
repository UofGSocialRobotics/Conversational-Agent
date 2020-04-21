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

function extractItemsSinglePage() {
	try{
		const extractedElements = document.querySelectorAll('a.recipe-review-author');
		const items = [];
		for (let element of extractedElements) {
			var i = element.href;
			if (items.indexOf(i) == -1) items.push(i);
		}
		return items;
	} catch(e){
		console.log("Error extractItemsSinglePage");
		console.log(e);
	}
}

function enoughItems(items, n_min=10){
	return (items.length >= 10);
}

async function extractItemsPageIdx(idx_page, page, url){
	try{
		const new_url = url + idx_page.toString();
		await page.goto(new_url);
		const items = await page.evaluate(extractItemsSinglePage);	
		console.log(items.length);
		return items;
	} catch(e){
		console.log("Error extractItemsPageIdx");
		console.log(e);
	}
}

async function extractItemsPageIdxNTrials(idx_page, page, url, n_trials_max){
	try{
		console.log("Trying to extract from page", idx_page);
		var tried_n_times = 0;
		while(true){
			tried_n_times++;
			const items = await extractItemsPageIdx(idx_page, page, url);	
			enoughItemsBool = enoughItems(items);
			if(tried_n_times >= n_trials_max || enoughItemsBool) {
				return items;
			}
		}
	} catch(e){
		console.log("Error extractItemsPageIdxNTrials");
		console.log(e);
	}
}


async function extractItemsPages(idx_pasges_to_try, page, url, n_trials_max){
	const all_items = [];
	const cant_get_pages = [];

	for (let idx_page of idx_pasges_to_try){
		const items = await extractItemsPageIdxNTrials(idx_page, page, url, n_trials_max);
		if (enoughItems(items)){
			for (i of items){
				if (all_items.indexOf(i) == -1) all_items.push(i);
			}
		} else {
			console.log("Failed");
			cant_get_pages.push(idx_page);
		}
	}
	const data = {"all_items": all_items, "cant_get_pages": cant_get_pages};
	return data;	
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
	const url = 'https://www.allrecipes.com/recipe/19344/homemade-lasagna/?page='
	const n_pages = 28;
	const n_trials_max = 10;

	const idx_pasges_to_try = [];
	for (var i=2; i<=n_pages; i++) idx_pasges_to_try.push(i);

	console.log(idx_pasges_to_try);

	// const all_items = [];
	const data = await extractItemsPages(idx_pasges_to_try, page, url, n_trials_max);
	const all_items = data["all_items"];
	const cant_get_pages = data['cant_get_pages'];

	// const moreBtn = await page.$('div.recipe-reviews__more-container > div.more-button');
	// await page.$eval('div.recipe-reviews__more-container > div.more-button', e => e.click());
	// await page.$eval('div.recipe-reviews__more-container > div.more-button', e => e.click());
	// await page.$eval('div.recipe-reviews__more-container > div.more-button', e => e.click());
	// console.log(moreBtn);

	try{
		console.log(all_items.length);
		console.log(cant_get_pages);
	} catch(e) {
		console.log(e);
	}

	const new_data = await extractItemsPages(cant_get_pages, page, url, n_trials_max);
	const new_all_items = data["all_items"];
	const new_cant_get_pages = data['cant_get_pages'];


	try{
		console.log(new_all_items.length);
		console.log(new_cant_get_pages);
	} catch(e) {
		console.log(e);
	}
	// for (let idx of cant_get_pages){
	// 	const new_url = 
	// 	const new_url = url + idx_page.toString();
	// 	console.log(new_url);
	// 	await page.goto(new_url);
	// 	const items = await page.evaluate(extractItemsSinglePage);	
	// 	const n_reviews = items.length;
	// 	console.log(items.length);
	// 	for (i of items){
	// 		if (all_items.indexOf(i) == -1) all_items.push(i);
	// 	}
	// }

	await browser.close();

})();