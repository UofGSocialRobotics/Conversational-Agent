const fs = require('fs');
const https = require('https')
const puppeteer = require('puppeteer');
const { PerformanceObserver, performance } = require('perf_hooks');

const n_trials_max = 5;

const page_size = 9;

const save_in = 'recipes_descriptions.json';
const allrecipes_ids_to_scrape_file_path = 'DBu30r25_ridsList.json';
const failed_path = 'mainrecipepage_failed.txt';


function extractRecipe(){
	const title = document.querySelectorAll('div.headline-wrapper > h1')[0].innerText;
	// n ratings & reviews
	const elts = document.querySelectorAll('ul.ugc-ratings-list > li');
	const n_ratings = parseInt(elts[0].innerText.replace( /[^\d.]/g, '' ));
	const n_reviews = parseInt(elts[1].innerText.replace( /[^\d.]/g, '' ));
	// image url
	const imageExtract = document.querySelectorAll('div.image-container > div')[0];
	const key_str = Object.keys(imageExtract)[0];
	const image_url = imageExtract[key_str]['src'];
	// Time info
	const asideExtract = document.querySelectorAll('aside.recipe-info-section');
	const col1Extract = asideExtract[0].querySelectorAll('div.two-subcol-content-wrapper > div');
	var time_info = {};
	for (let elt of col1Extract){
		const header = elt.querySelectorAll('div.recipe-meta-item-header')[0].innerText.trim().replace(/[.,\/#!$%\^&\*;:{}=\-_`~()]/g,"");
		const value = elt.querySelectorAll('div.recipe-meta-item-body')[0].innerText.trim().replace(/[.,\/#!$%\^&\*;:{}=\-_`~()]/g,"");
		time_info[header] = value;
	}
	// Instructions
	const instructionsExtract = document.querySelectorAll('ul.instructions-section > li > div.section-body');
	const instructions = [];
	for (let elt of instructionsExtract){
		instructions.push(elt.innerText.trim());
	}
	// ingredients
	const ingredientsExtract = document.querySelectorAll('ul.ingredients-section > li.ingredients-item');
	const ingredients = [];
	for (let elt of ingredientsExtract){
		ingredients.push(elt.innerText.trim());
	}
	// send res
	const new_recipe = {
		"title": title, 
		"n_ratings":n_ratings, 
		"n_reviews":n_reviews, 
		"image_url": image_url, 
		"time_info": time_info, 
		"ingredients": ingredients,
		"instructions": instructions};
	return new_recipe;
}

function extractDescription(){
	const description = document.querySelectorAll('p.margin-0-auto')[0].innerText;
	return description
}


function isDictInList(d, l){
	for (let elt of l){
		if (elt['id'] == d['id']) return true;
	}
	return false;
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

	// read list of recipes to scrap
	var contents = fs.readFileSync(allrecipes_ids_to_scrape_file_path);
	var json_contents = JSON.parse(contents);
	var idx_scraping = 0;
	var all_data = {};

	// read file of already scraped recipes
	const contents2 = fs.readFileSync(save_in);
	const json_already_scraped = JSON.parse(contents2);
	const already_scraped_ids = Object.keys(json_already_scraped);

	var n_errors = 0;

	for (let recipeid of json_contents){

		// if (idx_scraping > 13600){

		if (already_scraped_ids.indexOf(recipeid) == -1){

			console.log("\nIndex recipe:", idx_scraping);

			try{

				const url_main_page = 'https://www.allrecipes.com/recipe/'+recipeid;
				await page.goto(url_main_page);
				// const recipe_data = await page.evaluate(extractRecipe);
				const recipe_data = await page.evaluate(extractDescription);
				all_data[recipeid] = recipe_data;
				idx_scraping++;
				if(idx_scraping % 1 == 0 || idx_scraping == 1){
					console.log("Wrote to file:", save_in);
					const to_save = {...json_already_scraped, ...all_data};
					fs.writeFileSync(save_in, JSON.stringify(to_save));
				}

			} catch (e){
				fs.appendFile(failed_path, recipeid + "\n", function (err) {
					if (err) throw err;
					console.log('ERROR, could not collect main page for recipe, saved recipe\'s id to:', failed_path);
					if (n_errors > 2){
						n_errors = 0;
						idx_scraping++;
					} else {
						n_errors++;
					}
				});
			}
		}
		else {
			console.log("Passing: ", recipeid, idx_scraping++);
		}
		// }
		// else {
		// 	idx_scraping++;
		// }

	}
	

	await browser.close();

})();